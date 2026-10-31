# Sistema de Tickets

Aplicación de escritorio para atención al cliente y soporte técnico, hecha con
Python, SQLite y Tkinter (sin dependencias externas).

## Arquitectura

```text
modelo/       Entidades y repositorios SQLite
servicios/    Reglas de negocio (ServiceTicket, ServiceProducto, ServiceUsuario)
controlador/  Manejo de eventos de la interfaz
vista/        Componentes Tkinter/ttk
pruebas_unitarias/  Pruebas TDD de modelo y servicios
```

Flujo de dependencias: `vista → controlador → servicios → modelo`.

## Requisitos

- Python 3.10 o superior (probado con Python 3.13).
- Tkinter incluido en la instalación estándar de Python para Windows.

## Ejecución

```powershell
python app.py
```

La primera ejecución crea `tickets.db`, el esquema y los datos de ejemplo.
Si querés regenerar la base de demostración, eliminá `tickets.db` y volvé a
ejecutar la aplicación.

## Usuarios de demostración

La contraseña de todos los usuarios es `1234`.

| Email | Rol |
|---|---|
| ana@demo.com | Cliente |
| juan@demo.com | Cliente |
| sofia@demo.com | Cliente |
| carlos@demo.com | Representante (Línea blanca, Cocina) |
| lucia@demo.com | Representante (Electro, Pequeños electrodomésticos) |
| martin@demo.com | Representante (Línea blanca, Electro) |

## Reglas implementadas

- Solo los clientes crean tickets y eligen un representante del rubro.
- Cada ticket tiene cliente, representante, producto y tipo de producto.
- El representante debe estar especializado en el rubro del producto.
- Estados: `Abierto`, `en_Proceso`, `Cerrado`, `Finalizado`.
- Cliente y representante pueden cambiar el estado:
  - `Abierto → en_Proceso`.
  - `Abierto → Cerrado`.
  - `en_Proceso → Cerrado`.
  - `Cerrado → Finalizado` (solo el cliente).
  - `Cerrado → en_Proceso` (reapertura, ambos roles).
  - `Finalizado`: estado terminal.
- Cada cambio de estado genera un hito con usuario, estado anterior y nuevo.
- Cada mensaje enviado (incluido el mensaje inicial) genera un hito con autor,
  fecha y extracto del mensaje.
- Los mensajes generan alertas mediante el contador de no leídos.
- El cuadro «Conversación» es de solo lectura; los mensajes nuevos se escriben
  en el cuadro «Nuevo mensaje».

## Pruebas

```powershell
python run_tests.py
```

También se pueden ejecutar con:

```powershell
python -m unittest discover -s pruebas_unitarias -t . -v
```

## Notas y decisiones pendientes

El código incluye comentarios `TODO` en los puntos que la consigna no define:

- Si el mensaje inicial debe ser obligatorio.
- Si un ticket `Cerrado` debe seguir aceptando mensajes.
- Si los tickets `Finalizado` deben ocultarse o eliminarse del listado.

Los tickets finalizados se conservan como historial y no admiten acciones.
