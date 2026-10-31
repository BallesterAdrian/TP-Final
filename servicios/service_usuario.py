"""Servicio de usuarios y autenticación básica."""

import sqlite3

from modelo.entities import TipoProducto, Usuario
from modelo.repositories import UsuarioRepository
from servicios.errors import AuthenticationError, NotFoundError, ValidationError

ROLE_CUSTOMER = "Cliente"
ROLE_REPRESENTATIVE = "Representante"


class ServiceUsuario:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.users = UsuarioRepository(connection)

    def login(self, email: str, password: str, role: str) -> Usuario:
        """Valida email, contraseña y rol al iniciar la aplicación."""
        user = self.users.get_by_email(email.strip())
        if user is None or not user.check_password(password):
            raise AuthenticationError("Email o contraseña incorrectos.")

        if not user.activo:
            raise AuthenticationError("El usuario está inactivo.")

        if user.rol != role:
            raise AuthenticationError(
                "El rol seleccionado no coincide con el usuario."
            )

        return user

    def get_user(self, user_id: int) -> Usuario:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("No se encontró el usuario.")
        return user

    def list_customers(self) -> list[Usuario]:
        return self.users.list_by_role(ROLE_CUSTOMER)

    def list_product_types_for_representative(
        self, representative_id: int
    ) -> list[TipoProducto]:
        representative = self.get_user(representative_id)
        if representative.rol != ROLE_REPRESENTATIVE:
            raise ValidationError(
                "Solo los representantes tienen tipos de producto asignados."
            )
        return self.users.list_product_types_for_representative(representative_id)

    def is_specialist(self, representative_id: int, product_type_id: int) -> bool:
        return self.users.is_specialist(representative_id, product_type_id)
