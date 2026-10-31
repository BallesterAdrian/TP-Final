"""Pruebas de las reglas de negocio de tickets, hitos y mensajes."""

import unittest

from servicios.errors import PermissionDenied, ValidationError
from servicios.service_ticket import ServiceTicket
from pruebas_unitarias.base import (
    DatabaseTestCase,
    add_specialty,
    get_product_type_id,
    insert_product,
    insert_user,
)


class TestServiceTicket(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.white_line_id = get_product_type_id(self.connection, "Línea blanca")
        self.electro_id = get_product_type_id(self.connection, "Electro")
        self.product_id = insert_product(
            self.connection, "Heladera", self.white_line_id
        )
        self.customer_id = insert_user(
            self.connection, "Ana", "ana@demo.com", "Cliente"
        )
        self.other_customer_id = insert_user(
            self.connection, "Juan", "juan@demo.com", "Cliente"
        )
        self.representative_id = insert_user(
            self.connection, "Carlos", "carlos@demo.com", "Representante"
        )
        self.other_representative_id = insert_user(
            self.connection, "Lucía", "lucia@demo.com", "Representante"
        )
        add_specialty(self.connection, self.representative_id, self.white_line_id)
        add_specialty(
            self.connection, self.other_representative_id, self.electro_id
        )
        self.service = ServiceTicket(self.connection)

    def _create_ticket(self, initial_message=None):
        return self.service.create_ticket(
            representative_id=self.representative_id,
            customer_id=self.customer_id,
            product_id=self.product_id,
            subject="Heladera no enfría",
            initial_message=initial_message,
        )

    def test_create_ticket_starts_open_without_milestones(self):
        ticket_id = self._create_ticket()

        ticket = self.service.get_ticket(ticket_id, self.customer_id)

        self.assertEqual(ticket.estado, "Abierto")
        self.assertEqual(ticket.tipo_producto_id, self.white_line_id)
        self.assertEqual(self.service.list_milestones(ticket_id, self.customer_id), [])

    def test_initial_message_is_created_as_unread_for_representative(self):
        ticket_id = self._create_ticket("La heladera no enfría.")

        messages = self.service.list_messages(ticket_id, self.customer_id)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].autor_id, self.customer_id)
        self.assertFalse(messages[0].leido)
        self.assertEqual(
            self.service.count_unread(ticket_id, self.representative_id), 1
        )
        self.assertEqual(
            self.service.count_unread(ticket_id, self.customer_id), 0
        )

    def test_only_clients_can_create_tickets(self):
        # Un cliente no puede ocupar el lugar del representante.
        with self.assertRaises(ValidationError):
            self.service.create_ticket(
                customer_id=self.other_customer_id,
                representative_id=self.customer_id,
                product_id=self.product_id,
                subject="Cliente como representante",
            )

        # Un representante tampoco puede ser el cliente del ticket.
        with self.assertRaises(ValidationError):
            self.service.create_ticket(
                customer_id=self.representative_id,
                representative_id=self.representative_id,
                product_id=self.product_id,
                subject="Representante como cliente",
            )

    def test_representative_must_be_specialist(self):
        with self.assertRaises(ValidationError):
            self.service.create_ticket(
                representative_id=self.other_representative_id,
                customer_id=self.customer_id,
                product_id=self.product_id,
                subject="Rubro incorrecto",
            )

    def test_create_ticket_rejects_empty_subject(self):
        with self.assertRaises(ValidationError):
            self.service.create_ticket(
                representative_id=self.representative_id,
                customer_id=self.customer_id,
                product_id=self.product_id,
                subject="   ",
            )

    def test_create_ticket_rejects_inactive_customer(self):
        inactive_id = insert_user(
            self.connection,
            "Inactivo",
            "inactivo@demo.com",
            "Cliente",
            active=0,
        )

        with self.assertRaises(ValidationError):
            self.service.create_ticket(
                representative_id=self.representative_id,
                customer_id=inactive_id,
                product_id=self.product_id,
                subject="Cliente inactivo",
            )

    def test_send_message_updates_unread_counters(self):
        ticket_id = self._create_ticket()

        self.service.send_message(
            ticket_id, self.customer_id, "Sigue sin enfriar."
        )

        self.assertEqual(
            self.service.count_unread(ticket_id, self.representative_id), 1
        )
        self.assertEqual(
            self.service.count_unread(ticket_id, self.customer_id), 0
        )

        self.service.mark_messages_as_read(ticket_id, self.representative_id)

        self.assertEqual(
            self.service.count_unread(ticket_id, self.representative_id), 0
        )

    def test_non_party_cannot_send_messages(self):
        ticket_id = self._create_ticket()

        with self.assertRaises(PermissionDenied):
            self.service.send_message(
                ticket_id, self.other_customer_id, "No pertenezco al ticket."
            )

    def test_empty_message_is_rejected(self):
        ticket_id = self._create_ticket()

        with self.assertRaises(ValidationError):
            self.service.send_message(ticket_id, self.customer_id, "   ")

    def test_initial_message_creates_milestone(self):
        ticket_id = self._create_ticket("La heladera no enfría.")

        hitos = self.service.list_milestones(ticket_id, self.customer_id)

        self.assertEqual(len(hitos), 1)
        self.assertIsNone(hitos[0].estado_anterior)
        self.assertEqual(hitos[0].estado_nuevo, "Abierto")
        self.assertEqual(hitos[0].usuario_id, self.customer_id)
        self.assertIn("Mensaje inicial", hitos[0].detalle)

    def test_messages_from_both_parties_create_milestones(self):
        ticket_id = self._create_ticket()

        self.service.send_message(ticket_id, self.customer_id, "Sigue sin enfriar.")
        self.service.send_message(
            ticket_id, self.representative_id, "Revisamos el caso."
        )

        hitos = self.service.list_milestones(ticket_id, self.customer_id)

        self.assertEqual(len(hitos), 2)
        self.assertIsNone(hitos[0].estado_anterior)
        self.assertEqual(hitos[0].usuario_id, self.customer_id)
        self.assertIn("Sigue sin enfriar", hitos[0].detalle)
        self.assertEqual(hitos[1].usuario_id, self.representative_id)
        self.assertIn("Mensaje enviado", hitos[1].detalle)

    def test_representative_cannot_finalize_closed_ticket(self):
        ticket_id = self._create_ticket()
        self.service.change_status(
            ticket_id, self.representative_id, "en_Proceso"
        )
        self.service.change_status(ticket_id, self.representative_id, "Cerrado")

        with self.assertRaises(ValidationError):
            self.service.change_status(
                ticket_id, self.representative_id, "Finalizado"
            )

        ticket = self.service.get_ticket(ticket_id, self.customer_id)
        self.assertEqual(ticket.estado, "Cerrado")
        self.assertEqual(
            self.service.available_statuses(ticket_id, self.representative_id),
            ["en_Proceso"],
        )

    def test_representative_takes_case_and_milestone_is_created(self):
        ticket_id = self._create_ticket()

        self.service.change_status(
            ticket_id, self.representative_id, "en_Proceso", "Tomamos el caso"
        )

        ticket = self.service.get_ticket(ticket_id, self.customer_id)
        hitos = self.service.list_milestones(ticket_id, self.customer_id)

        self.assertEqual(ticket.estado, "en_Proceso")
        self.assertEqual(len(hitos), 1)
        self.assertEqual(hitos[0].estado_anterior, "Abierto")
        self.assertEqual(hitos[0].estado_nuevo, "en_Proceso")
        self.assertEqual(hitos[0].usuario_id, self.representative_id)

    def test_invalid_transition_does_not_change_ticket(self):
        ticket_id = self._create_ticket()

        with self.assertRaises(ValidationError):
            self.service.change_status(
                ticket_id, self.representative_id, "Finalizado"
            )

        ticket = self.service.get_ticket(ticket_id, self.customer_id)
        self.assertEqual(ticket.estado, "Abierto")
        self.assertEqual(
            self.service.list_milestones(ticket_id, self.customer_id), []
        )

    def test_both_parties_can_change_status(self):
        ticket_id = self._create_ticket()

        # El cliente abre el caso y lo pasa a en_Proceso.
        self.service.change_status(ticket_id, self.customer_id, "en_Proceso")
        # El representante lo cierra.
        self.service.change_status(ticket_id, self.representative_id, "Cerrado")
        # Solo el cliente puede finalizarlo.
        self.service.change_status(ticket_id, self.customer_id, "Finalizado")

        ticket = self.service.get_ticket(ticket_id, self.customer_id)
        self.assertEqual(ticket.estado, "Finalizado")

    def test_customer_can_close_ticket(self):
        ticket_id = self._create_ticket()

        self.service.change_status(ticket_id, self.customer_id, "Cerrado")

        ticket = self.service.get_ticket(ticket_id, self.customer_id)
        self.assertEqual(ticket.estado, "Cerrado")

    def test_customer_finalizes_closed_ticket(self):
        ticket_id = self._create_ticket()
        self.service.change_status(
            ticket_id, self.representative_id, "en_Proceso"
        )
        self.service.change_status(ticket_id, self.representative_id, "Cerrado")

        self.service.change_status(ticket_id, self.customer_id, "Finalizado")

        ticket = self.service.get_ticket(ticket_id, self.customer_id)
        hitos = self.service.list_milestones(ticket_id, self.customer_id)

        self.assertEqual(ticket.estado, "Finalizado")
        self.assertEqual(len(hitos), 3)
        self.assertEqual(hitos[-1].estado_anterior, "Cerrado")
        self.assertEqual(hitos[-1].estado_nuevo, "Finalizado")
        self.assertEqual(self.service.available_statuses(ticket_id, self.customer_id), [])
        self.assertEqual(
            self.service.available_statuses(ticket_id, self.representative_id), []
        )

        with self.assertRaises(ValidationError):
            self.service.change_status(
                ticket_id, self.customer_id, "en_Proceso"
            )

        with self.assertRaises(ValidationError):
            self.service.send_message(
                ticket_id, self.customer_id, "Mensaje en ticket finalizado."
            )

    def test_customer_reopens_closed_ticket(self):
        ticket_id = self._create_ticket()
        self.service.change_status(
            ticket_id, self.representative_id, "en_Proceso"
        )
        self.service.change_status(ticket_id, self.representative_id, "Cerrado")

        self.service.change_status(ticket_id, self.customer_id, "en_Proceso")

        ticket = self.service.get_ticket(ticket_id, self.customer_id)

        self.assertEqual(ticket.estado, "en_Proceso")
        self.assertEqual(
            self.service.available_statuses(ticket_id, self.representative_id),
            ["Cerrado"],
        )

    def test_available_statuses_depends_on_state(self):
        ticket_id = self._create_ticket()

        expected_open = ["en_Proceso", "Cerrado"]
        self.assertEqual(
            self.service.available_statuses(ticket_id, self.representative_id),
            expected_open,
        )
        self.assertEqual(
            self.service.available_statuses(ticket_id, self.customer_id),
            expected_open,
        )

        self.service.change_status(ticket_id, self.representative_id, "Cerrado")

        expected_closed = ["Finalizado", "en_Proceso"]
        self.assertEqual(
            self.service.available_statuses(ticket_id, self.customer_id),
            expected_closed,
        )
        # El representante puede reabrir, pero no finalizar.
        self.assertEqual(
            self.service.available_statuses(ticket_id, self.representative_id),
            ["en_Proceso"],
        )

    def test_list_tickets_for_customer_and_representative(self):
        ticket_id = self._create_ticket()

        customer_tickets = self.service.list_tickets_for_user(self.customer_id)
        representative_tickets = self.service.list_tickets_for_user(
            self.representative_id
        )

        self.assertEqual([ticket.id for ticket in customer_tickets], [ticket_id])
        self.assertEqual(
            [ticket.id for ticket in representative_tickets], [ticket_id]
        )


if __name__ == "__main__":
    unittest.main()
