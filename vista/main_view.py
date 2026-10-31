"""Vista principal: listado de tickets del usuario."""

import tkinter as tk
from tkinter import ttk

from vista.theme import STATUS_LABELS, format_datetime


class MainView(ttk.Frame):
    def __init__(
        self,
        parent,
        user,
        on_new_ticket,
        on_open_ticket,
        on_refresh,
        on_logout,
    ):
        super().__init__(parent, padding=20)
        self.user = user
        self.on_new_ticket = on_new_ticket
        self.on_open_ticket = on_open_ticket
        self.on_refresh = on_refresh
        self.on_logout = on_logout
        self._build()
        self.pack(fill="both", expand=True)

    def _build(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 16))

        ttk.Label(
            header, text=f"Hola, {self.user.nombre}", style="Header.TLabel"
        ).pack(side="left")
        ttk.Label(
            header, text=self.user.rol, style="Muted.TLabel"
        ).pack(side="left", padx=10, pady=(10, 0))
        ttk.Button(
            header, text="Cerrar sesión", command=self.on_logout
        ).pack(side="right")

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 12))

        self.new_ticket_button = ttk.Button(
            toolbar,
            text="Nuevo ticket",
            style="Accent.TButton",
            command=self.on_new_ticket,
        )
        self.new_ticket_button.pack(side="left")

        ttk.Button(
            toolbar, text="Abrir ticket", command=self._open_selected
        ).pack(side="left", padx=8)
        ttk.Button(
            toolbar, text="Refrescar lista", command=self.on_refresh
        ).pack(side="left")

        if self.user.rol != "Cliente":
            self.new_ticket_button.state(["disabled"])

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True)

        columns = (
            "id",
            "subject",
            "status",
            "customer",
            "representative",
            "product",
            "type",
            "unread",
            "updated",
        )
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )

        headings = {
            "id": "N°",
            "subject": "Asunto",
            "status": "Estado",
            "customer": "Cliente",
            "representative": "Representante",
            "product": "Producto",
            "type": "Tipo",
            "unread": "Sin leer",
            "updated": "Actualizado",
        }
        widths = {
            "id": 50,
            "subject": 250,
            "status": 100,
            "customer": 140,
            "representative": 140,
            "product": 160,
            "type": 130,
            "unread": 70,
            "updated": 130,
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=widths[column],
                minwidth=50,
                anchor="w" if column in {"subject", "product"} else "center",
                stretch=column in {"subject", "product"},
            )

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("unread", background="#fff7ed")
        self.tree.bind("<Double-1>", lambda _event: self._open_selected())
        self.tree.bind("<Return>", lambda _event: self._open_selected())

        self.status_label = ttk.Label(self, text="", style="Muted.TLabel")
        self.status_label.pack(fill="x", pady=(10, 0))

    def show_tickets(self, tickets) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_unread = 0
        for ticket in tickets:
            total_unread += ticket.sin_leer
            values = (
                ticket.id,
                ticket.asunto,
                STATUS_LABELS.get(ticket.estado, ticket.estado),
                ticket.cliente_nombre,
                ticket.representante_nombre,
                ticket.producto_nombre,
                ticket.tipo_producto_nombre,
                ticket.sin_leer if ticket.sin_leer else "",
                format_datetime(ticket.updated_at),
            )
            tags = ("unread",) if ticket.sin_leer else ()
            self.tree.insert(
                "", "end", iid=str(ticket.id), values=values, tags=tags
            )

        self.status_label.configure(
            text=(
                f"{len(tickets)} ticket(s) · "
                f"{total_unread} mensaje(s) sin leer"
            )
        )

    def get_selected_ticket_id(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _open_selected(self) -> None:
        ticket_id = self.get_selected_ticket_id()
        if ticket_id is None:
            self.status_label.configure(text="Seleccioná un ticket de la lista.")
            return
        self.on_open_ticket(ticket_id)

    def set_status(self, message: str) -> None:
        self.status_label.configure(text=message)
