"""Utilidades de seguridad para el login de la demo."""

import hashlib


def hash_password(password: str) -> str:
    """Devuelve el hash SHA-256 de una contraseña.

    Se usa la librería estándar para no agregar dependencias externas.
    # TODO: en un sistema real se debe usar bcrypt, scrypt o argon2.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
