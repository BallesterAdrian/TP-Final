"""Conexión e inicialización de la base SQLite."""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"
DEFAULT_DB_PATH = PROJECT_ROOT / "tickets.db"


class Database:
    """Administra la ruta de la base y la creación del esquema."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = str(db_path or DEFAULT_DB_PATH)

    def connect(self) -> sqlite3.Connection:
        """Abre una conexión con filas accesibles por nombre y FK activas."""
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self, with_seed: bool = False) -> None:
        """Crea las tablas si no existen y, opcionalmente, carga datos demo."""
        connection = self.connect()
        try:
            table = connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name = 'usuarios'
                """
            ).fetchone()

            if table is None:
                schema = SCHEMA_PATH.read_text(encoding="utf-8")
                connection.executescript(schema)
                connection.commit()

            if with_seed:
                # Importación local para evitar dependencias circulares.
                from modelo.seed import seed_demo_data

                seed_demo_data(connection)
                connection.commit()
        finally:
            connection.close()
