"""Pruebas de hitos (cambios de estado) y mensajes."""

import sqlite3
import unittest

from modelo.repositories import HitoRepository, MensajeRepository
from pruebas_unitarias.base import (
    DatabaseTestCase,
    get_product_type_id,
    insert_product,
    insert_ticket,
    insert_user,
)


class TestModeloHitosMensajes(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.hito_repo = HitoRepository(self.connection)
        self.message_repo = MensajeRepository(self.connection)
        self.product_type_id = get_product_type_id(self.connection, "Línea blanca")
        self.product_id = insert_product(
            self.connection, "Heladera", self.product_type_id
        )
        self.customer_id = insert_user(
            self.connection, "Ana", "ana@demo.com", "Cliente"
        )
        self.representative_id = insert_user(
            self.connection, "Carlos", "carlos@demo.com", "Representante"
        )
        self.ticket_id = insert_ticket(
            self.connection,
            self.customer_id,
            self.representative_id,
            self.product_id,
            self.product_type_id,
        )

    def test_create_and_list_milestone(self):
        hito_id = self.hito_repo.create(
            self.ticket_id,
            self.representative_id,
            "Abierto",
            "en_Proceso",
            "Tomamos el caso",
        )

        hitos = self.hito_repo.list_by_ticket(self.ticket_id)

        self.assertEqual(len(hitos), 1)
        self.assertEqual(hitos[0].id, hito_id)
        self.assertEqual(hitos[0].estado_anterior, "Abierto")
        self.assertEqual(hitos[0].estado_nuevo, "en_Proceso")
        self.assertEqual(hitos[0].usuario_nombre, "Carlos")

    def test_milestone_cannot_repeat_same_status(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.hito_repo.create(
                self.ticket_id,
                self.representative_id,
                "Abierto",
                "Abierto",
            )

    def test_empty_message_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.message_repo.create(self.ticket_id, self.representative_id, "   ")

    def test_mark_messages_as_read_for_reader(self):
        representative_message = self.message_repo.create(
            self.ticket_id, self.representative_id, "Respuesta del representante."
        )
        customer_message = self.message_repo.create(
            self.ticket_id, self.customer_id, "Respuesta del cliente."
        )

        self.message_repo.mark_as_read(self.ticket_id, self.customer_id)

        representative_row = self.connection.execute(
            "SELECT leido FROM mensajes WHERE id = ?", (representative_message,)
        ).fetchone()
        customer_row = self.connection.execute(
            "SELECT leido FROM mensajes WHERE id = ?", (customer_message,)
        ).fetchone()

        self.assertEqual(representative_row["leido"], 1)
        self.assertEqual(customer_row["leido"], 0)
        self.assertEqual(
            self.message_repo.count_unread(self.ticket_id, self.customer_id), 0
        )
        self.assertEqual(
            self.message_repo.count_unread(self.ticket_id, self.representative_id), 1
        )

    def test_messages_are_listed_in_chronological_order(self):
        first_id = self.message_repo.create(
            self.ticket_id, self.representative_id, "Primero"
        )
        second_id = self.message_repo.create(
            self.ticket_id, self.customer_id, "Segundo"
        )

        messages = self.message_repo.list_by_ticket(self.ticket_id)

        self.assertEqual([message.id for message in messages], [first_id, second_id])


if __name__ == "__main__":
    unittest.main()
