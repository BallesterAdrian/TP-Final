"""Vista de acceso: email, contraseña y rol."""

import tkinter as tk
from tkinter import ttk


class LoginView(ttk.Frame):
    def __init__(self, parent, on_login):
        super().__init__(parent, padding=32)
        self.on_login = on_login
        self._build()
        self.pack(fill="both", expand=True)

    def _build(self) -> None:
        container = ttk.Frame(self)
        container.pack(expand=True)

        ttk.Label(
            container, text="Sistema de Tickets", style="Header.TLabel"
        ).pack(pady=(0, 4))
        ttk.Label(
            container,
            text="Atención al cliente y soporte técnico",
            style="Muted.TLabel",
        ).pack(pady=(0, 28))

        form = ttk.Frame(container)
        form.pack(fill="x")

        ttk.Label(form, text="Email").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.email_entry = ttk.Entry(form, width=36)
        self.email_entry.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        ttk.Label(form, text="Contraseña").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.password_entry = ttk.Entry(form, width=36, show="*")
        self.password_entry.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        self.password_entry.bind("<Return>", lambda _event: self._submit())

        ttk.Label(form, text="Rol").grid(
            row=4, column=0, sticky="w", pady=(0, 4)
        )
        self.role_combo = ttk.Combobox(
            form,
            values=("Cliente", "Representante"),
            state="readonly",
            width=34,
        )
        self.role_combo.current(0)
        self.role_combo.grid(row=5, column=0, sticky="ew", pady=(0, 20))

        self.login_button = ttk.Button(
            form,
            text="Ingresar",
            style="Accent.TButton",
            command=self._submit,
        )
        self.login_button.grid(row=6, column=0, sticky="ew")

        self.error_label = ttk.Label(form, text="", style="Error.TLabel")
        self.error_label.grid(row=7, column=0, sticky="w", pady=(12, 0))

        ttk.Label(
            container,
            text=(
                "Usuarios de demo (contraseña 1234):\n"
                "ana@demo.com · Cliente     carlos@demo.com · Representante\n"
                "juan@demo.com · Cliente    lucia@demo.com · Representante"
            ),
            style="Muted.TLabel",
            justify="left",
        ).pack(pady=(28, 0))

        self.email_entry.focus_set()

    def _submit(self) -> None:
        self.on_login(
            self.email_entry.get().strip(),
            self.password_entry.get(),
            self.role_combo.get(),
        )

    def show_error(self, message: str) -> None:
        self.error_label.configure(text=message)
