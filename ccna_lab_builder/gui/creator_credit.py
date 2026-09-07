"""Visible project-origin attribution for the desktop application."""

from __future__ import annotations

import tkinter as tk

CREATOR = "Guillaume Paré"
CREDIT_TEXT = f"Original project vision, idea & concept by {CREATOR}"
CREDIT_SIDEBAR_TEXT = f"Original project vision,\nidea & concept by\n{CREATOR}"


def install_creator_credit(window):
    """Display a persistent project-origin credit in the sidebar and window title."""
    if getattr(window, "_creator_credit_installed", False):
        return window

    sidebar = getattr(window, "sidebar", None)
    if sidebar is not None:
        label = tk.Label(
            sidebar,
            text=CREDIT_SIDEBAR_TEXT,
            bg=window.SIDEBAR,
            fg=window.ACCENT,
            justify="left",
            font=(window.font_family, 8, "bold"),
        )
        label.pack(side="bottom", anchor="w", padx=20, pady=(0, 8))
        window._creator_credit_label = label

    root = window.winfo_toplevel()
    current_title = str(root.title() or "").strip()
    if CREDIT_TEXT not in current_title:
        root.title(f"{current_title} — {CREDIT_TEXT}" if current_title else CREDIT_TEXT)

    window._creator_credit_installed = True
    return window
