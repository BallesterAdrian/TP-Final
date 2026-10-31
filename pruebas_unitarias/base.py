"""Utilidades compartidas por las pruebas unitarias."""

import tempfile
import unittest
from pathlib import Path

from modelo.database import Database
from modelo.security import hash_password


class DatabaseTestCase(unittest.TestCase):
    """Crea una base SQLite temporal y limpia para cada prueba."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.database = Database(self.db_path)
        self.database.initialize(with_seed=False)
        self.connection = self.database.connect()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.connection.close()
        self.temp_dir.cleanup()


def insert_user(connection, name, email, role, active=1, password="1234"):
    cursor = connection.execute(
        """
        INSERT INTO usuarios (nombre, email, telefono, rol, activo, password_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, email, "555-0000", role, active, hash_password(password)),
    )
    connection.commit()
    return cursor.lastrowid


def get_product_type_id(connection, name="Línea blanca"):
    row = connection.execute(
        "SELECT id FROM tipos_producto WHERE nombre = ?", (name,)
    ).fetchone()
    return row["id"]


def insert_product(connection, name, product_type_id, brand="Marca", model="Modelo"):
    cursor = connection.execute(
        """
        INSERT INTO productos (nombre, marca, modelo, tipo_producto_id)
        VALUES (?, ?, ?, ?)
        """,
        (name, brand, model, product_type_id),
    )
    connection.commit()
    return cursor.lastrowid


def add_specialty(connection, representative_id, product_type_id):
    connection.execute(
        """
        INSERT INTO representante_tipo_producto (representante_id, tipo_producto_id)
        VALUES (?, ?)
        """,
        (representative_id, product_type_id),
    )
    connection.commit()


def insert_ticket(
    connection,
    customer_id,
    representative_id,
    product_id,
    product_type_id,
    subject="Ticket de prueba",
    status="Abierto",
):
    cursor = connection.execute(
        """
        INSERT INTO tickets
            (asunto, estado, cliente_id, representante_id, producto_id, tipo_producto_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (subject, status, customer_id, representative_id, product_id, product_type_id),
    )
    connection.commit()
    return cursor.lastrowid
