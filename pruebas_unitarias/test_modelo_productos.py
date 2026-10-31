"""Pruebas de productos y de la relación con su tipo."""

import sqlite3
import unittest

from modelo.repositories import ProductoRepository, UsuarioRepository
from pruebas_unitarias.base import (
    DatabaseTestCase,
    add_specialty,
    get_product_type_id,
    insert_product,
    insert_ticket,
    insert_user,
)


class TestModeloProductos(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.product_repo = ProductoRepository(self.connection)
        self.user_repo = UsuarioRepository(self.connection)

    def test_create_and_list_products_by_type(self):
        product_type_id = get_product_type_id(self.connection, "Cocina")

        product_id = self.product_repo.create_product(
            "Microondas", product_type_id, brand="Whirlpool", model="WM-20"
        )
        products = self.product_repo.list_products_by_type(product_type_id)

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, product_id)
        self.assertEqual(products[0].nombre, "Microondas")

    def test_product_with_unknown_type_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.product_repo.create_product("Producto raro", 9999)

    def test_ticket_rejects_product_type_mismatch(self):
        white_line_id = get_product_type_id(self.connection, "Línea blanca")
        kitchen_id = get_product_type_id(self.connection, "Cocina")
        product_id = insert_product(
            self.connection, "Heladera", white_line_id
        )
        customer_id = insert_user(
            self.connection, "Ana", "ana@demo.com", "Cliente"
        )
        representative_id = insert_user(
            self.connection, "Carlos", "carlos@demo.com", "Representante"
        )

        # El producto es de "Línea blanca" pero el ticket declara "Cocina".
        with self.assertRaises(sqlite3.IntegrityError):
            insert_ticket(
                self.connection,
                customer_id,
                representative_id,
                product_id,
                kitchen_id,
            )

    def test_list_representatives_by_product_type(self):
        product_type_id = get_product_type_id(self.connection, "Electro")
        representative_id = insert_user(
            self.connection, "Lucía", "lucia@demo.com", "Representante"
        )
        add_specialty(self.connection, representative_id, product_type_id)

        representatives = self.user_repo.list_representatives_by_product_type(
            product_type_id
        )

        self.assertEqual([representative.id for representative in representatives], [
            representative_id
        ])


if __name__ == "__main__":
    unittest.main()
