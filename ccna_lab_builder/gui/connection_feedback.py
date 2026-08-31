"""Non-blocking EVE-NG connection feedback for the desktop UI."""

from __future__ import annotations

import types
import tkinter as tk

from ccna_lab_builder.core.eve_api import EVEApi
from ccna_lab_builder.core.ssh import SSHConnection


VERSION = "4.6.2"


def _destroy_toast(window):
    job = getattr(window, "_connection_toast_job", None)
    if job is not None:
        try:
            window.after_cancel(job)
        except tk.TclError:
            pass
        window._connection_toast_job = None

    toast = getattr(window, "_connection_toast", None)
    if toast is not None:
        try:
            if toast.winfo_exists():
                toast.destroy()
        except tk.TclError:
            pass
        window._connection_toast = None


def _show_connection_toast(window, host, duration=4200):
    """Show a compact success toast in the top-right corner without taking focus."""
    _destroy_toast(window)

    bg = "#0F1B2D"
    border = "#24486E"
    toast = tk.Frame(
        window.main_area,
        bg=bg,
        highlightbackground=border,
        highlightthickness=1,
        bd=0,
    )
    window._connection_toast = toast

    icon = tk.Label(
        toast,
        text="✓",
        bg=bg,
        fg=window.SUCCESS,
        font=(window.font_family, 15, "bold"),
    )
    icon.grid(row=0, column=0, rowspan=2, padx=(14, 10), pady=10)

    title = tk.Label(
        toast,
        text="SSH + API CONNECTED",
        bg=bg,
        fg=window.TEXT,
        font=(window.font_family, 10, "bold"),
        anchor="w",
    )
    title.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=(9, 0))

    detail = tk.Label(
        toast,
        text=str(host),
        bg=bg,
        fg=window.MUTED,
        font=(window.font_family, 8),
        anchor="w",
    )
    detail.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=(0, 9))

    # Overlay the normal SSH/API pills briefly, then reveal them again.
    toast.place(relx=1.0, x=-24, y=18, anchor="ne")
    toast.lift()

    def dismiss(_event=None):
        _destroy_toast(window)
        return "break"

    for widget in (toast, icon, title, detail):
        widget.bind("<Button-1>", dismiss)

    window._connection_toast_job = window.after(
        int(duration),
        lambda: _destroy_toast(window),
    )


def _test_connection(self):
    """Run the existing SSH + API test but use non-blocking success feedback."""
    host = self.host.get().strip()
    if not host:
        raise ValueError("Enter the EVE-NG host.")
    if not self.ssh_user.get().strip():
        raise ValueError("Enter the SSH username.")
    if not self.api_user.get().strip():
        raise ValueError("Enter the EVE Web/API username.")

    self.log("Connecting via SSH...")
    self.ssh = SSHConnection(
        host,
        self.ssh_user.get().strip(),
        self.ssh_password.get(),
        self.ssh_port.get(),
    )
    try:
        hostname = self.ssh.connect()
    except Exception:
        self.after(0, lambda: self._set_connection_status(ssh=False, api=False))
        raise

    self.log(f"SSH OK: {hostname}")
    self.after(0, lambda: self._set_connection_status(ssh=True))

    self.log("Connecting to EVE-NG Web/API...")
    self.api = EVEApi(
        host,
        self.api_user.get().strip(),
        self.api_password.get(),
        https=self.https.get(),
    )
    try:
        self.api.login()
    except Exception:
        self.after(0, lambda: self._set_connection_status(api=False))
        raise

    self.log("EVE-NG API OK.")
    self.after(0, lambda: self._set_connection_status(api=True))

    self.settings.data["eve"].update(
        {
            "host": host,
            "ssh_port": int(self.ssh_port.get()),
            "ssh_username": self.ssh_user.get().strip(),
            "api_username": self.api_user.get().strip(),
            "https": self.https.get(),
        }
    )
    self.settings.save()

    self.after(0, lambda h=host: _show_connection_toast(self, h))


def install_connection_feedback(window):
    """Replace the modal success dialog with a top-right non-blocking toast."""
    if getattr(window, "_connection_feedback_installed", False):
        return window

    window.test_connection = types.MethodType(_test_connection, window)
    window.show_connection_toast = types.MethodType(
        lambda self, host, duration=4200: _show_connection_toast(self, host, duration),
        window,
    )
    window._connection_feedback_installed = True

    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except tk.TclError:
        pass

    return window
