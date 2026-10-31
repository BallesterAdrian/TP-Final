"""Estilos y utilidades visuales compartidas."""

import tkinter as tk
from datetime import datetime
from tkinter import ttk

COLOR_BG = "#f3f4f6"
COLOR_CARD = "#ffffff"
COLOR_TEXT = "#111827"
COLOR_MUTED = "#6b7280"
COLOR_ACCENT = "#0f766e"
COLOR_ACCENT_DARK = "#115e59"
COLOR_ERROR = "#b91c1c"

STATUS_LABELS = {
    "Abierto": "Abierto",
    "en_Proceso": "En proceso",
    "Cerrado": "Cerrado",
    "Finalizado": "Finalizado",
}

STATUS_COLORS = {
    "Abierto": "#1d4ed8",
    "en_Proceso": "#b45309",
    "Cerrado": "#4b5563",
    "Finalizado": "#15803d",
}


def apply_theme(root: tk.Tk) -> None:
    """Aplica un tema ttk limpio y consistente."""
    root.configure(background=COLOR_BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_CARD)
    style.configure(
        "TLabel",
        background=COLOR_BG,
        foreground=COLOR_TEXT,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT
    )
    style.configure(
        "Header.TLabel",
        font=("Segoe UI", 20, "bold"),
        background=COLOR_BG,
    )
    style.configure(
        "Subheader.TLabel",
        font=("Segoe UI", 12, "bold"),
        background=COLOR_BG,
    )
    style.configure(
        "Muted.TLabel",
        foreground=COLOR_MUTED,
        background=COLOR_BG,
        font=("Segoe UI", 9),
    )
    style.configure(
        "Error.TLabel",
        foreground=COLOR_ERROR,
        background=COLOR_BG,
        font=("Segoe UI", 9, "bold"),
    )
    style.configure("TButton", font=("Segoe UI", 10), padding=(12, 6))
    style.configure(
        "Accent.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=(14, 8),
        background=COLOR_ACCENT,
        foreground="white",
        borderwidth=0,
    )
    style.map(
        "Accent.TButton",
        background=[("active", COLOR_ACCENT_DARK)],
    )
    style.configure(
        "Treeview",
        font=("Segoe UI", 10),
        rowheight=28,
        background=COLOR_CARD,
        fieldbackground=COLOR_CARD,
    )
    style.configure(
        "Treeview.Heading",
        font=("Segoe UI", 10, "bold"),
        padding=(6, 6),
    )
    style.configure("TNotebook", background=COLOR_BG)
    style.configure(
        "TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(14, 8)
    )
    style.configure(
        "TLabelframe", background=COLOR_BG, bordercolor="#d1d5db"
    )
    style.configure(
        "TLabelframe.Label",
        background=COLOR_BG,
        foreground=COLOR_TEXT,
        font=("Segoe UI", 10, "bold"),
    )


def format_datetime(value: str) -> str:
    """Convierte 'YYYY-MM-DD HH:MM:SS' al formato visible de la interfaz."""
    if not value:
        return ""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value
    return parsed.strftime("%d/%m/%Y %H:%M")
