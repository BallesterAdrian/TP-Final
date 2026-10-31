"""Pruebas de la entidad Usuario y su acceso a datos."""

import sqlite3
import unittest

from modelo.entities import Cliente, Representante
from modelo.repositories import UsuarioRepository
from pruebas_unitarias.base import (
    DatabaseTestCase,
    add_specialty,
    get_product_type_id,
    insert_user,
)


class TestModeloUsuarios(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.repo = UsuarioRepository(self.connection)

    def test_repository_builds_customer_and_representative_subclasses(self):
        customer_id = insert_user(self.connection, "Ana", "ana@demo.com", "Cliente")
        representative_id = insert_user(
            self.connection, "Carlos", "carlos@demo.com", "Representante"
        )

        self.assertIsInstance(self.repo.get_by_id(customer_id), Cliente)
        self.assertIsInstance(self.repo.get_by_id(representative_id), Representante)

    def test_email_is_unique_ignoring_case(self):
        insert_user(self.connection, "Ana", "Ana@Demo.com", "Cliente")

        with self.assertRaises(sqlite3.IntegrityError):
            insert_user(self.connection, "Otra Ana", "ana@demo.com", "Cliente")

    def test_invalid_role_is_rejected_by_database(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_user(self.connection, "Pedro", "pedro@demo.com", "Supervisor")

    def test_get_by_email_is_case_insensitive(self):
        customer_id = insert_user(self.connection, "Ana", "ana@demo.com", "Cliente")

        user = self.repo.get_by_email("ANA@DEMO.COM")

        self.assertIsNotNone(user)
        self.assertEqual(user.id, customer_id)

    def test_representative_specialties(self):
        representative_id = insert_user(
            self.connection, "Carlos", "carlos@demo.com", "Representante"
        )
        product_type_id = get_product_type_id(self.connection, "Línea blanca")
        add_specialty(self.connection, representative_id, product_type_id)

        specialties = self.repo.list_product_types_for_representative(representative_id)

        self.assertEqual(len(specialties), 1)
        self.assertEqual(specialties[0].nombre, "Línea blanca")
        self.assertTrue(
            self.repo.is_specialist(representative_id, product_type_id)
        )

    def test_list_representatives_by_product_type(self):
        first_id = insert_user(
            self.connection, "Carlos", "carlos@demo.com", "Representante"
        )
        second_id = insert_user(
            self.connection, "Lucía", "lucia@demo.com", "Representante"
        )
        product_type_id = get_product_type_id(self.connection, "Electro")
        add_specialty(self.connection, first_id, product_type_id)

        representatives = self.repo.list_representatives_by_product_type(
            product_type_id
        )

        ids = [representative.id for representative in representatives]
        self.assertIn(first_id, ids)
        self.assertNotIn(second_id, ids)


if __name__ == "__main__":
    unittest.main()
