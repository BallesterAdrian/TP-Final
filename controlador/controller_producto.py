"""Controlador auxiliar para productos y tipos de producto."""

import sqlite3

from modelo.entities import Producto, TipoProducto, Usuario
from servicios.service_producto import ServiceProducto


class ControllerProducto:
    def __init__(self, connection: sqlite3.Connection, user: Usuario):
        self.service = ServiceProducto(connection)
        self.user = user

    def list_product_types(self) -> list[TipoProducto]:
        if self.user.rol == "Cliente":
            return self.service.list_product_types()
        return self.service.list_product_types_for_representative(self.user.id)

    def list_products(self, product_type_id: int) -> list[Producto]:
        return self.service.list_products_by_type(product_type_id)

    def list_representatives(self, product_type_id: int) -> list[Usuario]:
        return self.service.list_representatives_by_type(product_type_id)
