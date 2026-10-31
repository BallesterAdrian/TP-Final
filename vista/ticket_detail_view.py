"""Detalle del ticket: mensajes, hitos y acciones de estado."""

import tkinter as tk
from tkinter import ttk

from vista.theme import (
    STATUS_COLORS,
    STATUS_LABELS,
    format_datetime,
)


class TicketDetailView(tk.Toplevel):
    def __init__(self, parent, on_send, on_action, on_refresh):
        super().__init__(parent)
        self.on_send = on_send
        self.on_action = on_action
        self.on_refresh = on_refresh

        self.title("Detalle del ticket")
        self.geometry("880x720")
        self.minsize(740, 620)
        self.transient(parent)
        self._build()

    def _build(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        header = ttk.Frame(container)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.title_label = ttk.Label(
            header, text="", style="Header.TLabel"
        )
        self.title_label.pack(anchor="w")

        self.meta_label = ttk.Label(
            header,
            text="",
            style="Muted.TLabel",
            wraplength=780,
            justify="left",
        )
        self.meta_label.pack(anchor="w", pady=(4, 0))

        self.status_label = ttk.Label(
            header, text="", font=("Segoe UI", 11, "bold")
        )
        self.status_label.pack(anchor="w", pady=(6, 0))

        self.notebook = ttk.Notebook(container)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        messages_tab = ttk.Frame(self.notebook, padding=10)
        milestones_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(messages_tab, text="Mensajes")
        self.notebook.add(milestones_tab, text="Hitos")

        self._build_messages_tab(messages_tab)
        self._build_milestones_tab(milestones_tab)

        actions_box = ttk.LabelFrame(
            container, text="Cambiar estado del ticket", padding=8
        )
        actions_box.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.actions_frame = ttk.Frame(actions_box)
        self.actions_frame.pack(fill="x")

    def _build_messages_tab(self, parent) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        conversation = ttk.LabelFrame(
            parent, text="Conversación", padding=8
        )
        conversation.grid(row=0, column=0, sticky="nsew")

        text_frame = ttk.Frame(conversation)
        text_frame.pack(fill="both", expand=True)

        self.messages_text = tk.Text(
            text_frame,
            height=10,
            wrap="word",
            font=("Segoe UI", 10),
            state="disabled",
            background="#f9fafb",
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=8,
        )
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.messages_text.yview
        )
        self.messages_text.configure(yscrollcommand=scrollbar.set)
        self.messages_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.messages_text.tag_configure(
            "meta",
            foreground="#374151",
            font=("Segoe UI", 9, "bold"),
            spacing1=6,
        )
        self.messages_text.tag_configure("body", spacing3=10)
        self.messages_text.tag_configure(
            "empty", foreground="#6b7280", font=("Segoe UI", 10, "italic")
        )

        compose = ttk.LabelFrame(
            parent, text="Nuevo mensaje", padding=8
        )
        compose.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        compose.columnconfigure(0, weight=1)

        ttk.Label(
            compose,
            text=(
                "Escribí tu mensaje acá y presioná «Enviar mensaje» "
                "(o Ctrl+Enter)."
            ),
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.message_input = tk.Text(
            compose,
            height=3,
            wrap="word",
            font=("Segoe UI", 10),
            relief="solid",
            borderwidth=1,
            background="#ffffff",
        )
        self.message_input.grid(row=1, column=0, sticky="ew")
        self.message_input.bind(
            "<Control-Return>", lambda _event: self._send()
        )

        self.error_label = ttk.Label(
            compose, text="", style="Error.TLabel", wraplength=760
        )
        self.error_label.grid(row=2, column=0, sticky="ew", pady=(6, 0))

        input_buttons = ttk.Frame(compose)
        input_buttons.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self.send_button = ttk.Button(
            input_buttons,
            text="Enviar mensaje",
            style="Accent.TButton",
            command=self._send,
        )
        self.send_button.pack(side="right")

    def _build_milestones_tab(self, parent) -> None:
        columns = ("date", "previous", "new", "user", "detail")
        self.milestones_tree = ttk.Treeview(
            parent, columns=columns, show="headings", selectmode="browse"
        )
        headings = {
            "date": "Fecha",
            "previous": "Estado anterior",
            "new": "Estado nuevo",
            "user": "Usuario",
            "detail": "Detalle",
        }
        widths = {
            "date": 130,
            "previous": 120,
            "new": 120,
            "user": 160,
            "detail": 240,
        }
        for column in columns:
            self.milestones_tree.heading(column, text=headings[column])
            self.milestones_tree.column(
                column,
                width=widths[column],
                anchor="w" if column in {"user", "detail"} else "center",
            )

        scrollbar = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=self.milestones_tree.yview,
        )
        self.milestones_tree.configure(yscrollcommand=scrollbar.set)
        self.milestones_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def render(self, ticket, summary, hitos, messages, actions) -> None:
        self.current_ticket = ticket
        self.title_label.configure(text=f"Ticket #{ticket.id} · {ticket.asunto}")
        self.meta_label.configure(
            text=(
                f"Cliente: {summary.cliente_nombre}   |   "
                f"Representante: {summary.representante_nombre}   |   "
                f"Producto: {summary.producto_nombre}   |   "
                f"Tipo: {summary.tipo_producto_nombre}"
            )
        )
        self.status_label.configure(
            text=f"Estado: {STATUS_LABELS.get(ticket.estado, ticket.estado)}",
            foreground=STATUS_COLORS.get(ticket.estado, "#111827"),
        )

        self._render_messages(messages)
        self._render_milestones(hitos)
        self._render_actions(actions)
        self._update_input_state(ticket.estado)

    def _render_messages(self, messages) -> None:
        self.messages_text.configure(state="normal")
        self.messages_text.delete("1.0", "end")

        if not messages:
            self.messages_text.insert(
                "end", "Todavía no hay mensajes en este ticket.", "empty"
            )
        else:
            for message in messages:
                self.messages_text.insert(
                    "end",
                    (
                        f"{message.autor_nombre} ({message.autor_rol}) · "
                        f"{format_datetime(message.created_at)}\n"
                    ),
                    "meta",
                )
                self.messages_text.insert("end", f"{message.cuerpo}\n", "body")

        self.messages_text.configure(state="disabled")
        self.messages_text.see("end")

    def _render_milestones(self, hitos) -> None:
        for item in self.milestones_tree.get_children():
            self.milestones_tree.delete(item)

        if not hitos:
            self.milestones_tree.insert(
                "",
                "end",
                values=(
                    "",
                    "",
                    "",
                    "Sin hitos todavía",
                    "Se registrarán al cambiar el estado.",
                ),
            )
            return

        for hito in hitos:
            # Los hitos de mensaje no cambian de estado (estado_anterior NULL).
            is_message = hito.estado_anterior is None
            self.milestones_tree.insert(
                "",
                "end",
                values=(
                    format_datetime(hito.created_at),
                    (
                        "—"
                        if is_message
                        else STATUS_LABELS.get(
                            hito.estado_anterior, hito.estado_anterior
                        )
                    ),
                    (
                        "—"
                        if is_message
                        else STATUS_LABELS.get(hito.estado_nuevo, hito.estado_nuevo)
                    ),
                    hito.usuario_nombre,
                    hito.detalle or "",
                ),
            )

    def _render_actions(self, actions) -> None:
        for child in self.actions_frame.winfo_children():
            child.destroy()

        ttk.Button(
            self.actions_frame,
            text="Cerrar ventana",
            command=self.destroy,
        ).pack(side="right")
        ttk.Button(
            self.actions_frame, text="Actualizar", command=self.on_refresh
        ).pack(side="right", padx=(0, 6))

        for status, label in actions:
            ttk.Button(
                self.actions_frame,
                text=label,
                style="Accent.TButton",
                command=lambda selected=status: self.on_action(selected),
            ).pack(side="left", padx=(0, 8))

        if not actions:
            ttk.Label(
                self.actions_frame,
                text="No hay acciones de estado disponibles.",
                style="Muted.TLabel",
            ).pack(side="left")

    def _update_input_state(self, status: str) -> None:
        finished = status == "Finalizado"
        state = "disabled" if finished else "normal"
        self.message_input.configure(state=state)
        self.send_button.configure(
            state="disabled" if finished else "normal"
        )

        if finished:
            self.error_label.configure(
                text="El ticket está finalizado; solo puede consultarse."
            )
        else:
            self.error_label.configure(text="")
            self.after(100, self.message_input.focus_set)

    def _send(self) -> None:
        body = self.message_input.get("1.0", "end").strip()
        if not body:
            self.show_error("El mensaje no puede estar vacío.")
            self.message_input.focus_set()
            return

        self.show_error("")
        self.on_send(body)

    def clear_message(self) -> None:
        self.message_input.delete("1.0", "end")
        self.message_input.focus_set()

    def show_error(self, message: str) -> None:
        self.error_label.configure(text=message)
