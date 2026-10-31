"""Datos de ejemplo para probar la aplicación sin cargar todo a mano."""

import sqlite3

from modelo.security import hash_password


def _get_product_type_id(connection: sqlite3.Connection, name: str) -> int:
    row = connection.execute(
        "SELECT id FROM tipos_producto WHERE nombre = ?", (name,)
    ).fetchone()
    return row["id"]


def _get_user_id(connection: sqlite3.Connection, email: str) -> int:
    row = connection.execute(
        "SELECT id FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    return row["id"]


def _ensure_product(
    connection: sqlite3.Connection,
    name: str,
    product_type_id: int,
    brand: str,
    model: str,
) -> int:
    row = connection.execute(
        """
        SELECT id FROM productos
        WHERE nombre = ? AND tipo_producto_id = ?
        """,
        (name, product_type_id),
    ).fetchone()
    if row:
        return row["id"]

    cursor = connection.execute(
        """
        INSERT INTO productos (nombre, marca, modelo, tipo_producto_id)
        VALUES (?, ?, ?, ?)
        """,
        (name, brand, model, product_type_id),
    )
    return cursor.lastrowid


def seed_demo_data(connection: sqlite3.Connection) -> None:
    """Carga rubros, usuarios, especialidades y productos de demostración."""
    password_hash = hash_password("1234")

    product_types = [
        ("Línea blanca", "Heladeras, lavarropas y lavavajillas"),
        ("Cocina", "Hornos, microondas y cocinas"),
        ("Electro", "Televisores, equipos de audio y video"),
        ("Pequeños electrodomésticos", "Licuadoras, tostadoras y similares"),
    ]
    for name, description in product_types:
        connection.execute(
            """
            INSERT OR IGNORE INTO tipos_producto (nombre, descripcion)
            VALUES (?, ?)
            """,
            (name, description),
        )

    users = [
        ("Ana Rodríguez", "ana@demo.com", "555-1001", "Cliente"),
        ("Juan Martínez", "juan@demo.com", "555-1002", "Cliente"),
        ("Sofía López", "sofia@demo.com", "555-1003", "Cliente"),
        ("Carlos Gómez", "carlos@demo.com", "555-2001", "Representante"),
        ("Lucía Fernández", "lucia@demo.com", "555-2002", "Representante"),
        ("Martín Pérez", "martin@demo.com", "555-2003", "Representante"),
    ]
    for name, email, phone, role in users:
        connection.execute(
            """
            INSERT OR IGNORE INTO usuarios
                (nombre, email, telefono, rol, activo, password_hash)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (name, email, phone, role, password_hash),
        )

    white_line_id = _get_product_type_id(connection, "Línea blanca")
    kitchen_id = _get_product_type_id(connection, "Cocina")
    electro_id = _get_product_type_id(connection, "Electro")
    small_appliance_id = _get_product_type_id(
        connection, "Pequeños electrodomésticos"
    )

    carlos_id = _get_user_id(connection, "carlos@demo.com")
    lucia_id = _get_user_id(connection, "lucia@demo.com")
    martin_id = _get_user_id(connection, "martin@demo.com")

    specialties = [
        (carlos_id, white_line_id),
        (carlos_id, kitchen_id),
        (lucia_id, electro_id),
        (lucia_id, small_appliance_id),
        (martin_id, white_line_id),
        (martin_id, electro_id),
    ]
    for representative_id, product_type_id in specialties:
        connection.execute(
            """
            INSERT OR IGNORE INTO representante_tipo_producto
                (representante_id, tipo_producto_id)
            VALUES (?, ?)
            """,
            (representative_id, product_type_id),
        )

    products = [
        ("Heladera No Frost", white_line_id, "Samsung", "RT-32"),
        ("Lavarropas 8 kg", white_line_id, "Drean", "Next-8"),
        ("Horno eléctrico", kitchen_id, "BGH", "HE-55"),
        ("Microondas 20 L", kitchen_id, "Whirlpool", "WM-20"),
        ("Televisor 50 pulgadas", electro_id, "LG", "50UR"),
        ("Licuadora", small_appliance_id, "Moulinex", "LM-1"),
        ("Tostadora", small_appliance_id, "Philips", "HD-2"),
    ]
    for name, product_type_id, brand, model in products:
        _ensure_product(connection, name, product_type_id, brand, model)

    ticket_count = connection.execute(
        "SELECT COUNT(*) AS total FROM tickets"
    ).fetchone()["total"]

    if ticket_count == 0:
        ana_id = _get_user_id(connection, "ana@demo.com")
        heladera_id = _ensure_product(
            connection, "Heladera No Frost", white_line_id, "Samsung", "RT-32"
        )
        cursor = connection.execute(
            """
            INSERT INTO tickets
                (asunto, estado, cliente_id, representante_id,
                 producto_id, tipo_producto_id)
            VALUES (?, 'Abierto', ?, ?, ?, ?)
            """,
            (
                "Heladera no enfría",
                ana_id,
                carlos_id,
                heladera_id,
                white_line_id,
            ),
        )
        ticket_id = cursor.lastrowid
        connection.execute(
            """
            INSERT INTO mensajes (ticket_id, autor_id, cuerpo)
            VALUES (?, ?, ?)
            """,
            (
                ticket_id,
                ana_id,
                "Hola, la heladera dejó de enfriar. ¿Pueden revisarla?",
            ),
        )
