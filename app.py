"""Punto de entrada de la aplicación de tickets."""

import tkinter as tk
from tkinter import messagebox

from controlador.controller_login import ControllerLogin
from modelo.database import Database
from vista.theme import apply_theme


def main() -> None:
    root = tk.Tk()
    apply_theme(root)
    root.minsize(480, 560)

    database = Database()
    try:
        database.initialize(with_seed=True)
    except Exception as error:  # pragma: no cover - solo para mostrar el error
        messagebox.showerror(
            "Error de base de datos",
            f"No se pudo inicializar la base de datos:\n{error}",
        )
        root.destroy()
        return

    connection = database.connect()
    controller = ControllerLogin(root, connection)
    controller.start()

    try:
        root.mainloop()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
