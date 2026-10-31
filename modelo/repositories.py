"""Repositorios: traducen entre las entidades y las tablas SQLite."""

import sqlite3

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
from modelo.security import hash_password


def _build_user(row: sqlite3.Row) -> Usuario:
    """Convierte una fila de usuarios en Cliente o Representante."""
    role = row["rol"]
    if role == "Cliente":
        user_class = Cliente
    elif role == "Representante":
        user_class = Representante
    else:
        raise ValueError(f"Rol desconocido: {role}")

    return user_class(
        id=row["id"],
        nombre=row["nombre"],
        email=row["email"],
        telefono=row["telefono"],
        rol=role,
        activo=bool(row["activo"]),
        password_hash=row["password_hash"],
    )


class UsuarioRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def get_by_id(self, user_id: int) -> Usuario | None:
        row = self.connection.execute(
            "SELECT * FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
        return _build_user(row) if row else None

    def get_by_email(self, email: str) -> Usuario | None:
        row = self.connection.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email.strip(),)
        ).fetchone()
        return _build_user(row) if row else None

    def list_by_role(self, role: str) -> list[Usuario]:
        rows = self.connection.execute(
            """
            SELECT * FROM usuarios
            WHERE rol = ? AND activo = 1
            ORDER BY nombre
            """,
            (role,),
        ).fetchall()
        return [_build_user(row) for row in rows]

    def create(
        self,
        name: str,
        email: str,
        role: str,
        password: str,
        phone: str | None = None,
        active: bool = True,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO usuarios (nombre, email, telefono, rol, activo, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, email, phone, role, int(active), hash_password(password)),
        )
        return cursor.lastrowid

    def list_representatives_by_product_type(
        self, product_type_id: int
    ) -> list[Usuario]:
        rows = self.connection.execute(
            """
            SELECT u.*
            FROM usuarios u
            JOIN representante_tipo_producto rtp
                ON rtp.representante_id = u.id
            WHERE rtp.tipo_producto_id = ?
              AND u.rol = 'Representante'
              AND u.activo = 1
            ORDER BY u.nombre
            """,
            (product_type_id,),
        ).fetchall()
        return [_build_user(row) for row in rows]

    def list_product_types_for_representative(
        self, representative_id: int
    ) -> list[TipoProducto]:
        rows = self.connection.execute(
            """
            SELECT tp.*
            FROM tipos_producto tp
            JOIN representante_tipo_producto rtp
                ON rtp.tipo_producto_id = tp.id
            WHERE rtp.representante_id = ?
            ORDER BY tp.nombre
            """,
            (representative_id,),
        ).fetchall()
        return [
            TipoProducto(
                id=row["id"],
                nombre=row["nombre"],
                descripcion=row["descripcion"],
            )
            for row in rows
        ]

    def is_specialist(self, representative_id: int, product_type_id: int) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM representante_tipo_producto
            WHERE representante_id = ? AND tipo_producto_id = ?
            """,
            (representative_id, product_type_id),
        ).fetchone()
        return row is not None


class ProductoRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def list_product_types(self) -> list[TipoProducto]:
        rows = self.connection.execute(
            "SELECT * FROM tipos_producto ORDER BY nombre"
        ).fetchall()
        return [
            TipoProducto(
                id=row["id"],
                nombre=row["nombre"],
                descripcion=row["descripcion"],
            )
            for row in rows
        ]

    def get_product_type(self, product_type_id: int) -> TipoProducto | None:
        row = self.connection.execute(
            "SELECT * FROM tipos_producto WHERE id = ?", (product_type_id,)
        ).fetchone()
        if row is None:
            return None
        return TipoProducto(
            id=row["id"],
            nombre=row["nombre"],
            descripcion=row["descripcion"],
        )

    def create_product_type(
        self, name: str, description: str | None = None
    ) -> int:
        cursor = self.connection.execute(
            "INSERT INTO tipos_producto (nombre, descripcion) VALUES (?, ?)",
            (name, description),
        )
        return cursor.lastrowid

    def list_products_by_type(self, product_type_id: int) -> list[Producto]:
        rows = self.connection.execute(
            """
            SELECT * FROM productos
            WHERE tipo_producto_id = ?
            ORDER BY nombre
            """,
            (product_type_id,),
        ).fetchall()
        return [self._build_product(row) for row in rows]

    def get_product(self, product_id: int) -> Producto | None:
        row = self.connection.execute(
            "SELECT * FROM productos WHERE id = ?", (product_id,)
        ).fetchone()
        return self._build_product(row) if row else None

    def create_product(
        self,
        name: str,
        product_type_id: int,
        brand: str | None = None,
        model: str | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO productos (nombre, marca, modelo, tipo_producto_id)
            VALUES (?, ?, ?, ?)
            """,
            (name, brand, model, product_type_id),
        )
        return cursor.lastrowid

    @staticmethod
    def _build_product(row: sqlite3.Row) -> Producto:
        return Producto(
            id=row["id"],
            nombre=row["nombre"],
            tipo_producto_id=row["tipo_producto_id"],
            marca=row["marca"],
            modelo=row["modelo"],
        )


class TicketRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(
        self,
        subject: str,
        customer_id: int,
        representative_id: int,
        product_id: int,
        product_type_id: int,
        status: str = "Abierto",
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO tickets
                (asunto, estado, cliente_id, representante_id,
                 producto_id, tipo_producto_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                subject,
                status,
                customer_id,
                representative_id,
                product_id,
                product_type_id,
            ),
        )
        return cursor.lastrowid

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        row = self.connection.execute(
            "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        if row is None:
            return None
        return Ticket(
            id=row["id"],
            asunto=row["asunto"],
            estado=row["estado"],
            cliente_id=row["cliente_id"],
            representante_id=row["representante_id"],
            producto_id=row["producto_id"],
            tipo_producto_id=row["tipo_producto_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def update_status(self, ticket_id: int, status: str) -> None:
        self.connection.execute(
            """
            UPDATE tickets
            SET estado = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (status, ticket_id),
        )

    def touch(self, ticket_id: int) -> None:
        self.connection.execute(
            """
            UPDATE tickets
            SET updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (ticket_id,),
        )

    def list_by_customer(self, customer_id: int) -> list[TicketSummary]:
        return self._list_summaries("t.cliente_id = ?", customer_id, customer_id)

    def list_by_representative(
        self, representative_id: int
    ) -> list[TicketSummary]:
        return self._list_summaries(
            "t.representante_id = ?", representative_id, representative_id
        )

    def get_summary(self, ticket_id: int, viewer_id: int) -> TicketSummary | None:
        row = self.connection.execute(
            self._summary_query("t.id = ?"),
            (viewer_id, ticket_id),
        ).fetchone()
        return self._build_summary(row) if row else None

    def _list_summaries(
        self, where_clause: str, party_id: int, viewer_id: int
    ) -> list[TicketSummary]:
        rows = self.connection.execute(
            self._summary_query(where_clause),
            (viewer_id, party_id),
        ).fetchall()
        return [self._build_summary(row) for row in rows]

    @staticmethod
    def _summary_query(where_clause: str) -> str:
        return f"""
            SELECT
                t.id,
                t.asunto,
                t.estado,
                t.updated_at,
                c.nombre AS cliente_nombre,
                r.nombre AS representante_nombre,
                p.nombre AS producto_nombre,
                tp.nombre AS tipo_producto_nombre,
                (
                    SELECT COUNT(*)
                    FROM mensajes m
                    WHERE m.ticket_id = t.id
                      AND m.leido = 0
                      AND m.autor_id <> ?
                ) AS sin_leer
            FROM tickets t
            JOIN usuarios c ON c.id = t.cliente_id
            JOIN usuarios r ON r.id = t.representante_id
            JOIN productos p ON p.id = t.producto_id
            JOIN tipos_producto tp ON tp.id = t.tipo_producto_id
            WHERE {where_clause}
            ORDER BY t.updated_at DESC, t.id DESC
        """

    @staticmethod
    def _build_summary(row: sqlite3.Row) -> TicketSummary:
        return TicketSummary(
            id=row["id"],
            asunto=row["asunto"],
            estado=row["estado"],
            cliente_nombre=row["cliente_nombre"],
            representante_nombre=row["representante_nombre"],
            producto_nombre=row["producto_nombre"],
            tipo_producto_nombre=row["tipo_producto_nombre"],
            sin_leer=row["sin_leer"],
            updated_at=row["updated_at"],
        )


class HitoRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(
        self,
        ticket_id: int,
        user_id: int,
        previous_status: str | None,
        new_status: str,
        detail: str | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO hitos
                (ticket_id, usuario_id, estado_anterior, estado_nuevo, detalle)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_id, user_id, previous_status, new_status, detail),
        )
        return cursor.lastrowid

    def list_by_ticket(self, ticket_id: int) -> list[Hito]:
        rows = self.connection.execute(
            """
            SELECT h.*, u.nombre AS usuario_nombre
            FROM hitos h
            JOIN usuarios u ON u.id = h.usuario_id
            WHERE h.ticket_id = ?
            ORDER BY h.id
            """,
            (ticket_id,),
        ).fetchall()
        return [
            Hito(
                id=row["id"],
                ticket_id=row["ticket_id"],
                usuario_id=row["usuario_id"],
                usuario_nombre=row["usuario_nombre"],
                estado_anterior=row["estado_anterior"],
                estado_nuevo=row["estado_nuevo"],
                detalle=row["detalle"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class MensajeRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, ticket_id: int, author_id: int, body: str) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO mensajes (ticket_id, autor_id, cuerpo)
            VALUES (?, ?, ?)
            """,
            (ticket_id, author_id, body),
        )
        return cursor.lastrowid

    def list_by_ticket(self, ticket_id: int) -> list[Mensaje]:
        rows = self.connection.execute(
            """
            SELECT m.*, u.nombre AS autor_nombre, u.rol AS autor_rol
            FROM mensajes m
            JOIN usuarios u ON u.id = m.autor_id
            WHERE m.ticket_id = ?
            ORDER BY m.id
            """,
            (ticket_id,),
        ).fetchall()
        return [
            Mensaje(
                id=row["id"],
                ticket_id=row["ticket_id"],
                autor_id=row["autor_id"],
                autor_nombre=row["autor_nombre"],
                autor_rol=row["autor_rol"],
                cuerpo=row["cuerpo"],
                leido=bool(row["leido"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def mark_as_read(self, ticket_id: int, reader_id: int) -> None:
        self.connection.execute(
            """
            UPDATE mensajes
            SET leido = 1
            WHERE ticket_id = ? AND autor_id <> ? AND leido = 0
            """,
            (ticket_id, reader_id),
        )

    def count_unread(self, ticket_id: int, reader_id: int) -> int:
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM mensajes
            WHERE ticket_id = ? AND autor_id <> ? AND leido = 0
            """,
            (ticket_id, reader_id),
        ).fetchone()
        return row["total"]
