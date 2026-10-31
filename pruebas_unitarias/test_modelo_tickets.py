"""Pruebas de tickets, estados y consultas de listado."""

import sqlite3
import unittest

from modelo.repositories import TicketRepository
from pruebas_unitarias.base import (
    DatabaseTestCase,
    get_product_type_id,
    insert_product,
    insert_ticket,
    insert_user,
)


class TestModeloTickets(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.repo = TicketRepository(self.connection)
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

    def test_create_ticket_defaults_to_open(self):
        ticket_id = self.repo.create(
            subject="Heladera no enfría",
            customer_id=self.customer_id,
            representative_id=self.representative_id,
            product_id=self.product_id,
            product_type_id=self.product_type_id,
        )

        ticket = self.repo.get_by_id(ticket_id)

        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.estado, "Abierto")
        self.assertEqual(ticket.tipo_producto_id, self.product_type_id)

    def test_invalid_status_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_ticket(
                self.connection,
                self.customer_id,
                self.representative_id,
                self.product_id,
                self.product_type_id,
                status="Pendiente",
            )

    def test_customer_and_representative_must_be_different(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_ticket(
                self.connection,
                self.customer_id,
                self.customer_id,
                self.product_id,
                self.product_type_id,
            )

    def test_deleting_ticket_cascades_to_milestones_and_messages(self):
        ticket_id = insert_ticket(
            self.connection,
            self.customer_id,
            self.representative_id,
            self.product_id,
            self.product_type_id,
        )
        self.connection.execute(
            """
            INSERT INTO hitos
                (ticket_id, usuario_id, estado_anterior, estado_nuevo)
            VALUES (?, ?, 'Abierto', 'en_Proceso')
            """,
            (ticket_id, self.representative_id),
        )
        self.connection.execute(
            """
            INSERT INTO mensajes (ticket_id, autor_id, cuerpo)
            VALUES (?, ?, 'Mensaje')
            """,
            (ticket_id, self.representative_id),
        )
        self.connection.commit()

        self.connection.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
        self.connection.commit()

        hitos = self.connection.execute(
            "SELECT COUNT(*) AS total FROM hitos WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()["total"]
        mensajes = self.connection.execute(
            "SELECT COUNT(*) AS total FROM mensajes WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()["total"]

        self.assertEqual(hitos, 0)
        self.assertEqual(mensajes, 0)

    def test_list_summaries_by_customer_and_representative(self):
        ticket_id = self.repo.create(
            "Heladera no enfría",
            self.customer_id,
            self.representative_id,
            self.product_id,
            self.product_type_id,
        )
        self.connection.execute(
            """
            INSERT INTO mensajes (ticket_id, autor_id, cuerpo)
            VALUES (?, ?, 'Estamos revisando el caso.')
            """,
            (ticket_id, self.representative_id),
        )
        self.connection.commit()

        customer_tickets = self.repo.list_by_customer(self.customer_id)
        representative_tickets = self.repo.list_by_representative(
            self.representative_id
        )

        self.assertEqual(len(customer_tickets), 1)
        self.assertEqual(customer_tickets[0].id, ticket_id)
        self.assertEqual(customer_tickets[0].sin_leer, 1)
        self.assertEqual(representative_tickets[0].sin_leer, 0)

    def test_get_summary(self):
        ticket_id = self.repo.create(
            "Heladera no enfría",
            self.customer_id,
            self.representative_id,
            self.product_id,
            self.product_type_id,
        )

        summary = self.repo.get_summary(ticket_id, self.customer_id)

        self.assertIsNotNone(summary)
        self.assertEqual(summary.cliente_nombre, "Ana")
        self.assertEqual(summary.producto_nombre, "Heladera")


if __name__ == "__main__":
    unittest.main()
