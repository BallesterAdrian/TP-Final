"""Pruebas del servicio de productos."""

import unittest

from servicios.errors import ValidationError
from servicios.service_producto import ServiceProducto
from pruebas_unitarias.base import (
    DatabaseTestCase,
    add_specialty,
    get_product_type_id,
    insert_user,
)


class TestServiceProducto(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = ServiceProducto(self.connection)
        self.representative_id = insert_user(
            self.connection, "Carlos", "carlos@demo.com", "Representante"
        )
        self.customer_id = insert_user(
            self.connection, "Ana", "ana@demo.com", "Cliente"
        )

    def test_list_seeded_product_types(self):
        product_types = self.service.list_product_types()

        self.assertEqual(len(product_types), 4)
        names = [product_type.nombre for product_type in product_types]
        self.assertIn("Línea blanca", names)
        self.assertIn("Pequeños electrodomésticos", names)

    def test_create_product_and_list_by_type(self):
        product_type_id = get_product_type_id(self.connection, "Cocina")

        product_id = self.service.create_product(
            "Microondas", product_type_id, brand="Whirlpool", model="WM-20"
        )
        products = self.service.list_products_by_type(product_type_id)

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, product_id)

    def test_create_product_rejects_empty_name(self):
        product_type_id = get_product_type_id(self.connection, "Cocina")

        with self.assertRaises(ValidationError):
            self.service.create_product("   ", product_type_id)

    def test_create_product_rejects_unknown_type(self):
        with self.assertRaises(ValidationError):
            self.service.create_product("Producto raro", 9999)

    def test_list_product_types_for_representative(self):
        product_type_id = get_product_type_id(self.connection, "Electro")
        add_specialty(self.connection, self.representative_id, product_type_id)

        product_types = self.service.list_product_types_for_representative(
            self.representative_id
        )

        self.assertEqual(len(product_types), 1)
        self.assertEqual(product_types[0].id, product_type_id)

    def test_list_product_types_for_customer_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.service.list_product_types_for_representative(self.customer_id)

    def test_list_representatives_by_type(self):
        product_type_id = get_product_type_id(self.connection, "Electro")
        add_specialty(self.connection, self.representative_id, product_type_id)

        representatives = self.service.list_representatives_by_type(product_type_id)

        self.assertEqual(len(representatives), 1)
        self.assertEqual(representatives[0].id, self.representative_id)


if __name__ == "__main__":
    unittest.main()
