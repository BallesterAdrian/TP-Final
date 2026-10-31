"""Errores de negocio que los controladores muestran al usuario."""


class ServiceError(Exception):
    """Error base de la capa de servicios."""


class ValidationError(ServiceError):
    """Los datos recibidos no cumplen una regla de negocio."""


class AuthenticationError(ServiceError):
    """El email, la contraseña o el rol no son válidos."""


class PermissionDenied(ServiceError):
    """El usuario no tiene permiso para realizar la acción."""


class NotFoundError(ServiceError):
    """No se encontró el registro solicitado."""
