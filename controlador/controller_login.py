"""Controlador de la ventana de acceso."""

import sqlite3
import tkinter as tk

from controlador.controller_ticket import ControllerTicket
from servicios.errors import ServiceError
from servicios.service_usuario import ServiceUsuario
from vista.login_view import LoginView


class ControllerLogin:
    def __init__(self, root: tk.Tk, connection: sqlite3.Connection):
        self.root = root
        self.connection = connection
        self.service = ServiceUsuario(connection)
        self.login_view = None
        self.ticket_controller = None

    def start(self) -> None:
        self._show_login()

    def _show_login(self) -> None:
        self._clear_root()
        self.ticket_controller = None
        self.root.title("Sistema de Tickets · Acceso")
        self.root.geometry("480x600")
        self.login_view = LoginView(self.root, self._attempt_login)
        self.root.deiconify()

    def _attempt_login(self, email: str, password: str, role: str) -> None:
        try:
            user = self.service.login(email, password, role)
        except ServiceError as error:
            self.login_view.show_error(str(error))
            return

        self._clear_root()
        self.ticket_controller = ControllerTicket(
            self.root, self.connection, user, self._show_login
        )
        self.ticket_controller.start()

    def _clear_root(self) -> None:
        self.login_view = None
        for child in self.root.winfo_children():
            child.destroy()
