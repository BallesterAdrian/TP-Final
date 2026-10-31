"""Entidades del dominio, sin dependencias de SQLite ni de Tkinter."""

from abc import ABC
from dataclasses import dataclass

from modelo.security import hash_password


@dataclass
class Usuario(ABC):
    """Clase abstracta que representa a cualquier usuario del sistema."""

    id: int | None
    nombre: str
    email: str
    telefono: str | None
    rol: str
    activo: bool = True
    password_hash: str = ""

    def check_password(self, password: str) -> bool:
        """Compara una contraseña en texto plano contra el hash guardado."""
        return self.password_hash == hash_password(password)


@dataclass
class Cliente(Usuario):
    """Usuario con rol Cliente."""


@dataclass
class Representante(Usuario):
    """Usuario con rol Representante."""


@dataclass
class TipoProducto:
    id: int | None
    nombre: str
    descripcion: str | None = None


@dataclass
class Producto:
    id: int | None
    nombre: str
    tipo_producto_id: int
    marca: str | None = None
    modelo: str | None = None


@dataclass
class Ticket:
    id: int | None
    asunto: str
    estado: str
    cliente_id: int
    representante_id: int
    producto_id: int
    tipo_producto_id: int
    created_at: str = ""
    updated_at: str = ""


@dataclass
class TicketSummary:
    """Datos ya unidos para mostrar en la lista de tickets."""

    id: int
    asunto: str
    estado: str
    cliente_nombre: str
    representante_nombre: str
    producto_nombre: str
    tipo_producto_nombre: str
    sin_leer: int
    updated_at: str


@dataclass
class Hito:
    """Registro de actividad de un ticket: cambio de estado o mensaje."""

    id: int
    ticket_id: int
    usuario_id: int
    usuario_nombre: str
    estado_anterior: str | None
    estado_nuevo: str
    detalle: str | None
    created_at: str


@dataclass
class Mensaje:
    id: int
    ticket_id: int
    autor_id: int
    autor_nombre: str
    autor_rol: str
    cuerpo: str
    leido: bool
    created_at: str
