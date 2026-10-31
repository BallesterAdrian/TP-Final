"""Servicio de tickets: creación, mensajes, hitos y cambios de estado."""

import sqlite3

from modelo.entities import Hito, Mensaje, Ticket, TicketSummary, Usuario
from modelo.repositories import (
    HitoRepository,
    MensajeRepository,
    ProductoRepository,
    TicketRepository,
    UsuarioRepository,
)
from servicios.errors import NotFoundError, PermissionDenied, ValidationError
from servicios.service_usuario import ROLE_CUSTOMER, ROLE_REPRESENTATIVE

STATUS_OPEN = "Abierto"
STATUS_IN_PROGRESS = "en_Proceso"
STATUS_CLOSED = "Cerrado"
STATUS_FINISHED = "Finalizado"

# Transiciones permitidas: estado nuevo -> roles que pueden ejecutarla.
# Finalizado es terminal y solo el cliente puede finalizar el ticket.
TRANSITIONS = {
    STATUS_OPEN: {
        STATUS_IN_PROGRESS: (ROLE_CUSTOMER, ROLE_REPRESENTATIVE),
        STATUS_CLOSED: (ROLE_CUSTOMER, ROLE_REPRESENTATIVE),
    },
    STATUS_IN_PROGRESS: {
        STATUS_CLOSED: (ROLE_CUSTOMER, ROLE_REPRESENTATIVE),
    },
    STATUS_CLOSED: {
        STATUS_FINISHED: (ROLE_CUSTOMER,),
        STATUS_IN_PROGRESS: (ROLE_CUSTOMER, ROLE_REPRESENTATIVE),
    },
    STATUS_FINISHED: {},
}


class ServiceTicket:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.tickets = TicketRepository(connection)
        self.hitos = HitoRepository(connection)
        self.messages = MensajeRepository(connection)
        self.users = UsuarioRepository(connection)
        self.products = ProductoRepository(connection)

    # ------------------------------------------------------------------
    # Creación y consultas
    # ------------------------------------------------------------------
    def create_ticket(
        self,
        customer_id: int,
        representative_id: int,
        product_id: int,
        subject: str,
        initial_message: str | None = None,
    ) -> int:
        customer = self.users.get_by_id(customer_id)
        if customer is None or customer.rol != ROLE_CUSTOMER or not customer.activo:
            raise ValidationError(
                "Solo un cliente activo puede crear tickets."
            )

        representative = self.users.get_by_id(representative_id)
        if (
            representative is None
            or representative.rol != ROLE_REPRESENTATIVE
            or not representative.activo
        ):
            raise ValidationError(
                "El representante seleccionado no es válido."
            )

        product = self.products.get_product(product_id)
        if product is None:
            raise ValidationError("El producto seleccionado no existe.")

        if not self.users.is_specialist(
            representative_id, product.tipo_producto_id
        ):
            raise ValidationError(
                "El representante no está especializado en este tipo de producto."
            )

        clean_subject = subject.strip()
        if not clean_subject:
            raise ValidationError("El asunto es obligatorio.")

        # TODO: confirmar si el mensaje inicial debe ser obligatorio.
        clean_message = initial_message.strip() if initial_message else None
        if clean_message == "":
            clean_message = None

        try:
            with self.connection:
                ticket_id = self.tickets.create(
                    subject=clean_subject,
                    customer_id=customer_id,
                    representative_id=representative_id,
                    product_id=product_id,
                    product_type_id=product.tipo_producto_id,
                )
                if clean_message:
                    # El mensaje inicial lo escribe el cliente que abre la consulta.
                    self.messages.create(ticket_id, customer_id, clean_message)
                    self.hitos.create(
                        ticket_id,
                        customer_id,
                        None,
                        STATUS_OPEN,
                        self._message_detail("Mensaje inicial", clean_message),
                    )
        except sqlite3.IntegrityError as error:
            raise ValidationError(
                "No se pudo crear el ticket con esos datos."
            ) from error

        return ticket_id

    def list_tickets_for_user(self, user_id: int) -> list[TicketSummary]:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("No se encontró el usuario.")

        # TODO: confirmar si "deja de existir al finalizar" implica ocultar
        # o eliminar los tickets Finalizado del listado.
        if user.rol == ROLE_CUSTOMER:
            return self.tickets.list_by_customer(user_id)
        if user.rol == ROLE_REPRESENTATIVE:
            return self.tickets.list_by_representative(user_id)

        raise ValidationError("El rol del usuario no es válido.")

    def get_ticket(self, ticket_id: int, viewer_id: int) -> Ticket:
        ticket = self._get_ticket(ticket_id)
        self._assert_party(ticket, viewer_id)
        return ticket

    def get_summary(self, ticket_id: int, viewer_id: int) -> TicketSummary:
        self.get_ticket(ticket_id, viewer_id)
        summary = self.tickets.get_summary(ticket_id, viewer_id)
        if summary is None:
            raise NotFoundError("No se encontró el ticket.")
        return summary

    def list_milestones(self, ticket_id: int, viewer_id: int) -> list[Hito]:
        self.get_ticket(ticket_id, viewer_id)
        return self.hitos.list_by_ticket(ticket_id)

    def list_messages(self, ticket_id: int, viewer_id: int) -> list[Mensaje]:
        self.get_ticket(ticket_id, viewer_id)
        return self.messages.list_by_ticket(ticket_id)

    # ------------------------------------------------------------------
    # Mensajes y alertas
    # ------------------------------------------------------------------
    def send_message(self, ticket_id: int, author_id: int, body: str) -> int:
        ticket = self.get_ticket(ticket_id, author_id)

        if ticket.estado == STATUS_FINISHED:
            raise ValidationError(
                "El ticket está finalizado y no admite nuevos mensajes."
            )

        # TODO: confirmar si un ticket Cerrado debe seguir aceptando mensajes.
        clean_body = body.strip()
        if not clean_body:
            raise ValidationError("El mensaje no puede estar vacío.")

        with self.connection:
            message_id = self.messages.create(
                ticket_id, author_id, clean_body
            )
            self.hitos.create(
                ticket_id,
                author_id,
                None,
                ticket.estado,
                self._message_detail("Mensaje enviado", clean_body),
            )
            self.tickets.touch(ticket_id)

        return message_id

    def mark_messages_as_read(self, ticket_id: int, reader_id: int) -> None:
        self.get_ticket(ticket_id, reader_id)
        with self.connection:
            self.messages.mark_as_read(ticket_id, reader_id)

    def count_unread(self, ticket_id: int, reader_id: int) -> int:
        self.get_ticket(ticket_id, reader_id)
        return self.messages.count_unread(ticket_id, reader_id)

    # ------------------------------------------------------------------
    # Cambios de estado e hitos
    # ------------------------------------------------------------------
    def available_statuses(self, ticket_id: int, actor_id: int) -> list[str]:
        ticket = self.get_ticket(ticket_id, actor_id)
        actor = self.users.get_by_id(actor_id)
        if actor is None:
            raise NotFoundError("No se encontró el usuario.")

        return [
            new_status
            for new_status, allowed_roles in TRANSITIONS[ticket.estado].items()
            if actor.rol in allowed_roles
        ]

    def change_status(
        self,
        ticket_id: int,
        actor_id: int,
        new_status: str,
        detail: str | None = None,
    ) -> str:
        ticket = self.get_ticket(ticket_id, actor_id)
        allowed = self.available_statuses(ticket_id, actor_id)

        if new_status not in allowed:
            raise ValidationError(
                "El cambio de estado no está permitido para este usuario."
            )

        clean_detail = detail.strip() if detail else None
        if clean_detail == "":
            clean_detail = None

        with self.connection:
            self.tickets.update_status(ticket_id, new_status)
            self.hitos.create(
                ticket_id,
                actor_id,
                ticket.estado,
                new_status,
                clean_detail,
            )

        return new_status

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _get_ticket(self, ticket_id: int) -> Ticket:
        ticket = self.tickets.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("No se encontró el ticket.")
        return ticket

    @staticmethod
    def _message_detail(prefix: str, body: str) -> str:
        excerpt = body.replace("\n", " ").strip()
        if len(excerpt) > 100:
            excerpt = excerpt[:97] + "..."
        return f"{prefix}: {excerpt}"

    @staticmethod
    def _assert_party(ticket: Ticket, user_id: int) -> None:
        if user_id not in (ticket.cliente_id, ticket.representante_id):
            raise PermissionDenied(
                "No tiene permiso para acceder a este ticket."
            )
