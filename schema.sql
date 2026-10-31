-- ===============================================================
-- SISTEMA DE TICKETS - ESQUEMA SQLITE
-- Nombres de tablas y columnas en español para respetar el UML.
-- El código Python usa identificadores en inglés.
-- ===============================================================

PRAGMA foreign_keys = ON;

-- ===============================================================
-- USUARIOS
-- Herencia de la clase abstracta Usuario.
-- Cliente y Representante se diferencian por el campo rol.
-- El email es único en toda la tabla, sin distinguir mayúsculas.
-- ===============================================================
CREATE TABLE usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL,
    email         TEXT NOT NULL COLLATE NOCASE UNIQUE,
    telefono      TEXT,
    rol           TEXT NOT NULL CHECK (rol IN ('Cliente', 'Representante')),
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    password_hash TEXT NOT NULL CHECK (length(password_hash) > 0)
);

-- ===============================================================
-- TIPOS DE PRODUCTO
-- Rubros: línea blanca, cocina, electro, pequeños electrodomésticos.
-- ===============================================================
CREATE TABLE tipos_producto (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL UNIQUE,
    descripcion TEXT
);

-- ===============================================================
-- ESPECIALIDAD DE LOS REPRESENTANTES
-- Relación N:M entre representante y tipo de producto.
-- La validación de que el usuario tenga rol 'Representante'
-- se hace en la capa de Servicios.
-- ===============================================================
CREATE TABLE representante_tipo_producto (
    representante_id INTEGER NOT NULL,
    tipo_producto_id INTEGER NOT NULL,
    PRIMARY KEY (representante_id, tipo_producto_id),
    FOREIGN KEY (representante_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    FOREIGN KEY (tipo_producto_id) REFERENCES tipos_producto (id) ON DELETE CASCADE
);

-- ===============================================================
-- PRODUCTOS
-- Un tipo de producto tiene muchos productos.
-- La clave compuesta permite validar el tipo desde tickets.
-- ===============================================================
CREATE TABLE productos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre           TEXT NOT NULL,
    marca            TEXT,
    modelo           TEXT,
    tipo_producto_id INTEGER NOT NULL,
    FOREIGN KEY (tipo_producto_id) REFERENCES tipos_producto (id) ON DELETE RESTRICT,
    UNIQUE (id, tipo_producto_id)
);

-- ===============================================================
-- TICKETS
-- Estados exactos del enum del diagrama.
-- La FK compuesta garantiza que el tipo del ticket sea el mismo
-- que el tipo del producto elegido.
-- ===============================================================
CREATE TABLE tickets (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    asunto           TEXT NOT NULL CHECK (length(trim(asunto)) > 0),
    estado           TEXT NOT NULL DEFAULT 'Abierto'
                     CHECK (estado IN ('Abierto', 'en_Proceso', 'Cerrado', 'Finalizado')),
    cliente_id       INTEGER NOT NULL,
    representante_id INTEGER NOT NULL,
    producto_id      INTEGER NOT NULL,
    tipo_producto_id INTEGER NOT NULL,
    created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (cliente_id) REFERENCES usuarios (id) ON DELETE RESTRICT,
    FOREIGN KEY (representante_id) REFERENCES usuarios (id) ON DELETE RESTRICT,
    FOREIGN KEY (producto_id, tipo_producto_id)
        REFERENCES productos (id, tipo_producto_id) ON DELETE RESTRICT,

    CHECK (cliente_id <> representante_id)
);

-- ===============================================================
-- HITOS
-- Registro de actividad del ticket: cambios de estado y mensajes.
-- Para los hitos de mensaje estado_anterior queda NULL y estado_nuevo
-- guarda el estado vigente al momento de enviarlo.
-- ===============================================================
CREATE TABLE hitos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id       INTEGER NOT NULL,
    usuario_id      INTEGER NOT NULL,
    estado_anterior TEXT
                    CHECK (estado_anterior IS NULL OR
                           estado_anterior IN ('Abierto', 'en_Proceso', 'Cerrado', 'Finalizado')),
    estado_nuevo    TEXT NOT NULL
                    CHECK (estado_nuevo IN ('Abierto', 'en_Proceso', 'Cerrado', 'Finalizado')),
    detalle         TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE RESTRICT,

    CHECK (estado_anterior IS NULL OR estado_anterior <> estado_nuevo)
);

-- ===============================================================
-- MENSAJES
-- Comunicaciones del hilo del ticket.
-- leido = 0 indica que el destinatario todavía no lo leyó.
-- ===============================================================
CREATE TABLE mensajes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id  INTEGER NOT NULL,
    autor_id   INTEGER NOT NULL,
    cuerpo     TEXT NOT NULL CHECK (length(trim(cuerpo)) > 0),
    leido      INTEGER NOT NULL DEFAULT 0 CHECK (leido IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE,
    FOREIGN KEY (autor_id) REFERENCES usuarios (id) ON DELETE RESTRICT
);

-- ===============================================================
-- ÍNDICES
-- ===============================================================
CREATE INDEX idx_tickets_cliente       ON tickets (cliente_id, estado);
CREATE INDEX idx_tickets_representante ON tickets (representante_id, estado);
CREATE INDEX idx_hitos_ticket          ON hitos (ticket_id, created_at);
CREATE INDEX idx_mensajes_ticket       ON mensajes (ticket_id, created_at);
CREATE INDEX idx_mensajes_pendientes   ON mensajes (ticket_id, leido);

-- Catálogo inicial de rubros.
INSERT INTO tipos_producto (nombre) VALUES
    ('Línea blanca'),
    ('Cocina'),
    ('Electro'),
    ('Pequeños electrodomésticos');
