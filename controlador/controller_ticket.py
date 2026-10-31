"""Controlador principal de tickets."""

import sqlite3
import tkinter as tk
from tkinter import messagebox

from controlador.controller_producto import ControllerProducto
from modelo.entities import Usuario
from servicios.errors import ServiceError
from servicios.service_ticket import ServiceTicket
from vista.main_view import MainView
from vista.theme import STATUS_LABELS
from vista.ticket_detail_view import TicketDetailView
from vista.ticket_form_view import TicketFormView


class ControllerTicket:
    def __init__(
        self,
        root: tk.Tk,
        connection: sqlite3.Connection,
        user: Usuario,
        on_logout,
    ):
        self.root = root
        self.connection = connection
        self.user = user
        self.on_logout = on_logout

        self.service_ticket = ServiceTicket(connection)
        self.product_controller = ControllerProducto(connection, user)
        self.main_view = None
        self.ticket_form = None

    def start(self) -> None:
        self.root.title(f"Sistema de Tickets · {self.user.rol}")
        self.root.geometry("1180x720")
        self.main_view = MainView(
            self.root,
            self.user,
            on_new_ticket=self._new_ticket,
            on_open_ticket=self._open_ticket,
            on_refresh=self.refresh,
            on_logout=self._logout,
        )
        self.refresh()

    # ------------------------------------------------------------------
    # Listado
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        try:
            tickets = self.service_ticket.list_tickets_for_user(self.user.id)
        except ServiceError as error:
            messagebox.showerror("Error", str(error), parent=self.root)
            return
        self.main_view.show_tickets(tickets)

    # ------------------------------------------------------------------
    # Alta de ticket
    # ------------------------------------------------------------------
    def _new_ticket(self) -> None:
        if self.user.rol != "Cliente":
            messagebox.showinfo(
                "Permiso",
                "Solo los clientes pueden crear tickets.",
                parent=self.root,
            )
            return

        if self.ticket_form is not None and self.ticket_form.winfo_exists():
            self.ticket_form.lift()
            return

        try:
            product_types = self.product_controller.list_product_types()
        except ServiceError as error:
            messagebox.showerror("Error", str(error), parent=self.root)
            return

        if not product_types:
            messagebox.showwarning(
                "Sin rubros",
                "No hay tipos de producto cargados en el sistema.",
                parent=self.root,
            )
            return

        form = TicketFormView(
            self.root,
            product_types=product_types,
            on_save=lambda data: self._save_ticket(form, data),
            on_type_change=lambda type_id: self._load_options(form, type_id),
        )
        self.ticket_form = form
        form.trigger_type_change()

    def _load_options(self, form: TicketFormView, type_id: int) -> None:
        try:
            products = self.product_controller.list_products(type_id)
            representatives = self.product_controller.list_representatives(type_id)
        except ServiceError as error:
            form.show_error(str(error))
            return

        form.set_products(products)
        form.set_representatives(representatives)

        if not products:
            form.show_error("No hay productos cargados para este rubro.")
        elif not representatives:
            form.show_error(
                "No hay representantes disponibles para este rubro."
            )

    def _save_ticket(self, form: TicketFormView, data: dict) -> None:
        try:
            ticket_id = self.service_ticket.create_ticket(
                customer_id=self.user.id,
                representative_id=data["representative_id"],
                product_id=data["product_id"],
                subject=data["subject"],
                initial_message=data["initial_message"],
            )
        except ServiceError as error:
            form.show_error(str(error))
            return

        form.destroy()
        self.ticket_form = None
        self.refresh()
        self.main_view.set_status(f"Ticket #{ticket_id} creado correctamente.")

    # ------------------------------------------------------------------
    # Detalle del ticket
    # ------------------------------------------------------------------
    def _open_ticket(self, ticket_id: int) -> None:
        try:
            self.service_ticket.mark_messages_as_read(ticket_id, self.user.id)
            detail_data = self._load_detail(ticket_id)
        except ServiceError as error:
            messagebox.showerror("Error", str(error), parent=self.root)
            return

        self.refresh()

        view = TicketDetailView(
            self.root,
            on_send=lambda body: self._send_message(view, ticket_id, body),
            on_action=lambda status: self._change_status(
                view, ticket_id, status
            ),
            on_refresh=lambda: self._reload_detail(view, ticket_id),
        )
        view.render(*detail_data)

    def _load_detail(self, ticket_id: int):
        ticket = self.service_ticket.get_ticket(ticket_id, self.user.id)
        summary = self.service_ticket.get_summary(ticket_id, self.user.id)
        hitos = self.service_ticket.list_milestones(ticket_id, self.user.id)
        messages = self.service_ticket.list_messages(ticket_id, self.user.id)
        actions = self._build_actions(ticket)
        return ticket, summary, hitos, messages, actions

    def _build_actions(self, ticket) -> list[tuple[str, str]]:
        take_label = (
            "Tomar caso"
            if self.user.rol == "Representante"
            else "Marcar en proceso"
        )
        labels = {
            ("Abierto", "en_Proceso"): take_label,
            ("Abierto", "Cerrado"): "Cerrar ticket",
            ("en_Proceso", "Cerrado"): "Cerrar ticket",
            ("Cerrado", "Finalizado"): "Finalizar ticket",
            ("Cerrado", "en_Proceso"): "Reabrir ticket",
        }
        statuses = self.service_ticket.available_statuses(
            ticket.id, self.user.id
        )
        return [
            (
                status,
                labels.get(
                    (ticket.estado, status),
                    STATUS_LABELS.get(status, status),
                ),
            )
            for status in statuses
        ]

    def _reload_detail(self, view: TicketDetailView, ticket_id: int) -> None:
        if not view.winfo_exists():
            return

        try:
            self.service_ticket.mark_messages_as_read(ticket_id, self.user.id)
            detail_data = self._load_detail(ticket_id)
        except ServiceError as error:
            view.show_error(str(error))
            return

        view.render(*detail_data)
        self.refresh()

    def _send_message(
        self, view: TicketDetailView, ticket_id: int, body: str
    ) -> None:
        try:
            self.service_ticket.send_message(
                ticket_id, self.user.id, body
            )
        except ServiceError as error:
            view.show_error(str(error))
            return

        view.clear_message()
        self._reload_detail(view, ticket_id)

    def _change_status(
        self, view: TicketDetailView, ticket_id: int, new_status: str
    ) -> None:
        label = STATUS_LABELS.get(new_status, new_status)
        if not messagebox.askyesno(
            "Confirmar cambio",
            f"¿Cambiar el estado del ticket a «{label}»?",
            parent=view,
        ):
            return

        try:
            self.service_ticket.change_status(
                ticket_id, self.user.id, new_status
            )
        except ServiceError as error:
            view.show_error(str(error))
            return

        self._reload_detail(view, ticket_id)
        if self.main_view is not None:
            self.main_view.set_status(f"Estado actualizado a «{label}».")

    # ------------------------------------------------------------------
    # Sesión
    # ------------------------------------------------------------------
    def _logout(self) -> None:
        if not messagebox.askyesno(
            "Cerrar sesión",
            "¿Deseás cerrar la sesión actual?",
            parent=self.root,
        ):
            return

        if self.main_view is not None:
            self.main_view.destroy()
            self.main_view = None
        self.on_logout()
