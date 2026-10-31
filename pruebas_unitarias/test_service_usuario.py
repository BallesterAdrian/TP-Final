"""Pruebas del servicio de usuarios y del login."""

import unittest

from servicios.errors import AuthenticationError
from servicios.service_usuario import ServiceUsuario
from pruebas_unitarias.base import DatabaseTestCase, insert_user


class TestServiceUsuario(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = ServiceUsuario(self.connection)
        self.customer_id = insert_user(
            self.connection, "Ana", "ana@demo.com", "Cliente"
        )
        self.representative_id = insert_user(
            self.connection, "Carlos", "carlos@demo.com", "Representante"
        )

    def test_login_with_correct_email_password_and_role(self):
        user = self.service.login("ana@demo.com", "1234", "Cliente")

        self.assertEqual(user.id, self.customer_id)
        self.assertEqual(user.rol, "Cliente")

    def test_login_is_case_insensitive_for_email(self):
        user = self.service.login("ANA@DEMO.COM", "1234", "Cliente")

        self.assertEqual(user.id, self.customer_id)

    def test_login_rejects_wrong_password(self):
        with self.assertRaises(AuthenticationError):
            self.service.login("ana@demo.com", "incorrecta", "Cliente")

    def test_login_rejects_role_mismatch(self):
        with self.assertRaises(AuthenticationError):
            self.service.login("ana@demo.com", "1234", "Representante")

    def test_login_rejects_unknown_email(self):
        with self.assertRaises(AuthenticationError):
            self.service.login("nadie@demo.com", "1234", "Cliente")

    def test_login_rejects_inactive_user(self):
        insert_user(
            self.connection,
            "Inactivo",
            "inactivo@demo.com",
            "Cliente",
            active=0,
        )

        with self.assertRaises(AuthenticationError):
            self.service.login("inactivo@demo.com", "1234", "Cliente")

    def test_list_customers(self):
        customers = self.service.list_customers()

        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0].id, self.customer_id)


if __name__ == "__main__":
    unittest.main()
