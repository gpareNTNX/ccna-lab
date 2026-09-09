"""Windows-specific clipboard shortcuts for the interactive EVE-NG console."""

from __future__ import annotations

import platform
import tkinter as tk

from ccna_lab_builder.gui.console_workspace import TerminalSessionView


def _has_selection(view) -> bool:
    try:
        return bool(view.terminal.tag_ranges("sel"))
    except (tk.TclError, AttributeError):
        return False


def _handle_control_c(view, event=None, system_name: str | None = None):
    """Copy selected text on Windows; otherwise preserve IOS Ctrl+C interrupt."""
    system_name = system_name or platform.system()
    if system_name == "Windows" and _has_selection(view):
        return view._copy(event)
    view._send(b"\x03")
    return "break"


def _bind_windows_shortcuts(view) -> None:
    """Install deterministic Windows bindings after the VT compatibility layer."""
    view.terminal.bind(
        "<Control-c>",
        lambda event: _handle_control_c(view, event, "Windows"),
    )
    view.terminal.bind("<Control-v>", view._paste)
    view.terminal.bind("<Control-Shift-c>", view._copy)
    view.terminal.bind("<Control-Shift-C>", view._copy)
    view.terminal.bind("<Control-Shift-v>", view._paste)
    view.terminal.bind("<Control-Shift-V>", view._paste)


def _install_windows_console_shortcuts() -> None:
    if getattr(TerminalSessionView, "_windows_clipboard_shortcuts", False):
        return

    original_build = TerminalSessionView._build

    def build(view):
        original_build(view)
        if platform.system() == "Windows":
            _bind_windows_shortcuts(view)

    TerminalSessionView._build = build
    TerminalSessionView._windows_clipboard_shortcuts = True


def install_windows_console_shortcuts(window):
    """Install Windows clipboard behavior without changing macOS/Linux terminal keys."""
    _install_windows_console_shortcuts()
    return getattr(window, "_console_workspace", None)
