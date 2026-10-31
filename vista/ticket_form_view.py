"""Formulario de alta de ticket (solo clientes)."""

import tkinter as tk
from tkinter import ttk


class TicketFormView(tk.Toplevel):
    def __init__(
        self,
        parent,
        product_types,
        on_save,
        on_type_change,
    ):
        super().__init__(parent)
        self.on_save = on_save
        self.on_type_change = on_type_change
        self.product_types = list(product_types)
        self.products = []
        self.representatives = []

        self.title("Nuevo ticket")
        self.geometry("600x660")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        container = ttk.Frame(self, padding=24)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container, text="Nuevo ticket", style="Header.TLabel"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(
            container,
            text="La consulta quedará asociada a tu usuario como cliente.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 18))

        ttk.Label(container, text="Tipo de producto").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.type_combo = ttk.Combobox(
            container,
            state="readonly",
            values=[product_type.nombre for product_type in self.product_types],
        )
        self.type_combo.grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12)
        )
        self.type_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._type_changed()
        )

        ttk.Label(container, text="Producto").grid(
            row=4, column=0, sticky="w", pady=(0, 4)
        )
        self.product_combo = ttk.Combobox(container, state="readonly", values=[])
        self.product_combo.grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(0, 12)
        )

        ttk.Label(container, text="Representante").grid(
            row=6, column=0, sticky="w", pady=(0, 4)
        )
        self.representative_combo = ttk.Combobox(
            container, state="readonly", values=[]
        )
        self.representative_combo.grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(0, 12)
        )

        ttk.Label(container, text="Asunto").grid(
            row=8, column=0, sticky="w", pady=(0, 4)
        )
        self.subject_entry = ttk.Entry(container)
        self.subject_entry.grid(
            row=9, column=0, columnspan=2, sticky="ew", pady=(0, 12)
        )

        ttk.Label(container, text="Mensaje inicial (opcional)").grid(
            row=10, column=0, sticky="w", pady=(0, 4)
        )
        self.message_text = tk.Text(
            container,
            height=6,
            wrap="word",
            font=("Segoe UI", 10),
            relief="solid",
            borderwidth=1,
        )
        self.message_text.grid(
            row=11, column=0, columnspan=2, sticky="nsew", pady=(0, 12)
        )

        self.error_label = ttk.Label(
            container, text="", style="Error.TLabel", wraplength=540
        )
        self.error_label.grid(
            row=12, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        buttons = ttk.Frame(container)
        buttons.grid(row=13, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(
            side="right", padx=(8, 0)
        )
        ttk.Button(
            buttons,
            text="Crear ticket",
            style="Accent.TButton",
            command=self._save,
        ).pack(side="right")

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(11, weight=1)

        if self.product_types:
            self.type_combo.current(0)
        self.subject_entry.focus_set()

    def trigger_type_change(self) -> None:
        self._type_changed()

    def _type_changed(self) -> None:
        index = self.type_combo.current()
        if index < 0:
            return
        self.on_type_change(self.product_types[index].id)

    def set_products(self, products) -> None:
        self.products = list(products)
        self.product_combo["values"] = [
            self._product_label(product) for product in self.products
        ]
        if self.products:
            self.product_combo.current(0)
        else:
            self.product_combo.set("")

    def set_representatives(self, representatives) -> None:
        self.representatives = list(representatives)
        self.representative_combo["values"] = [
            f"{representative.nombre} ({representative.email})"
            for representative in self.representatives
        ]
        if self.representatives:
            self.representative_combo.current(0)
        else:
            self.representative_combo.set("")

    @staticmethod
    def _product_label(product) -> str:
        details = " / ".join(
            value for value in (product.marca, product.modelo) if value
        )
        return f"{product.nombre} ({details})" if details else product.nombre

    def _save(self) -> None:
        if self.product_combo.current() < 0:
            self.show_error("Seleccioná un producto.")
            return
        if self.representative_combo.current() < 0:
            self.show_error("Seleccioná un representante.")
            return

        product = self.products[self.product_combo.current()]
        representative = self.representatives[
            self.representative_combo.current()
        ]

        self.on_save(
            {
                "product_id": product.id,
                "representative_id": representative.id,
                "subject": self.subject_entry.get().strip(),
                "initial_message": self.message_text.get("1.0", "end").strip(),
            }
        )

    def show_error(self, message: str) -> None:
        self.error_label.configure(text=message)
