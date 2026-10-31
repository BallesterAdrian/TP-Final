"""Servicio de productos y tipos de producto."""

import sqlite3

from modelo.entities import Producto, TipoProducto, Usuario
from modelo.repositories import ProductoRepository, UsuarioRepository
from servicios.errors import ValidationError
from servicios.service_usuario import ROLE_REPRESENTATIVE


class ServiceProducto:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.products = ProductoRepository(connection)
        self.users = UsuarioRepository(connection)

    def list_product_types(self) -> list[TipoProducto]:
        return self.products.list_product_types()

    def get_product_type(self, product_type_id: int) -> TipoProducto:
        product_type = self.products.get_product_type(product_type_id)
        if product_type is None:
            raise ValidationError("El tipo de producto no existe.")
        return product_type

    def list_product_types_for_representative(
        self, representative_id: int
    ) -> list[TipoProducto]:
        representative = self.users.get_by_id(representative_id)
        if representative is None or representative.rol != ROLE_REPRESENTATIVE:
            raise ValidationError(
                "Solo los representantes tienen tipos de producto asignados."
            )
        return self.users.list_product_types_for_representative(representative_id)

    def list_products_by_type(self, product_type_id: int) -> list[Producto]:
        self.get_product_type(product_type_id)
        return self.products.list_products_by_type(product_type_id)

    def list_representatives_by_type(
        self, product_type_id: int
    ) -> list[Usuario]:
        self.get_product_type(product_type_id)
        return self.users.list_representatives_by_product_type(product_type_id)

    def get_product(self, product_id: int) -> Producto:
        product = self.products.get_product(product_id)
        if product is None:
            raise ValidationError("El producto no existe.")
        return product

    def create_product_type(
        self, name: str, description: str | None = None
    ) -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationError("El nombre del tipo de producto es obligatorio.")

        try:
            with self.connection:
                return self.products.create_product_type(
                    clean_name, description.strip() if description else None
                )
        except sqlite3.IntegrityError as error:
            raise ValidationError(
                "Ya existe un tipo de producto con ese nombre."
            ) from error

    def create_product(
        self,
        name: str,
        product_type_id: int,
        brand: str | None = None,
        model: str | None = None,
    ) -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationError("El nombre del producto es obligatorio.")

        self.get_product_type(product_type_id)

        try:
            with self.connection:
                return self.products.create_product(
                    clean_name,
                    product_type_id,
                    brand.strip() if brand else None,
                    model.strip() if model else None,
                )
        except sqlite3.IntegrityError as error:
            raise ValidationError(
                "No se pudo crear el producto con esos datos."
            ) from error
