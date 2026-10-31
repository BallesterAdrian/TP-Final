"""Capa modelo: entidades y acceso a datos."""

from modelo.database import Database
from modelo.entities import (
    Cliente,
    Hito,
    Mensaje,
    Producto,
    Representante,
    Ticket,
    TicketSummary,
    TipoProducto,
    Usuario,
)

__all__ = [
    "Cliente",
    "Database",
    "Hito",
    "Mensaje",
    "Producto",
    "Representante",
    "Ticket",
    "TicketSummary",
    "TipoProducto",
    "Usuario",
]
