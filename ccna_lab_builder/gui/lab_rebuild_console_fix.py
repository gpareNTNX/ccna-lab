"""Safe lab replacement and interactive-console recovery compatibility."""

from __future__ import annotations

import inspect
import threading
import time
import types
import tkinter as tk
from tkinter import ttk

from ccna_lab_builder.core.eve_api import EVEApi
from ccna_lab_builder.core.live_validation import LiveValidator
from ccna_lab_builder.gui.console_workspace import TerminalSessionView


VERSION = "4.6.0"
_INTERACTIVE_CONSOLE = threading.local()


def _is_missing_lab_error(exc):
    text = str(exc).lower()
    return "does not exist" in text or "60000" in text or "404" in text


def _delete_lab_method(self, lab):
    """Delete one existing EVE-NG lab using the documented DELETE endpoint."""
    return self.request("DELETE", "/labs/" + self._path(lab))


def _install_delete_lab_api():
    if not hasattr(EVEApi, "delete_lab"):
        EVEApi.delete_lab = _delete_lab_method


def _lab_exists(api, lab):
    try:
        api.get_lab(lab)
        return True
    except RuntimeError as exc:
        if _is_missing_lab_error(exc):
            return False
        raise


def _wait_until_deleted(api, lab, timeout=8.0, poll=0.25):
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        if not _lab_exists(api, lab):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(max(0.01, poll))


def _destroy_existing_lab(window, lab):
    """Stop, close and delete a lab so the builder can recreate it safely."""
    lab = str(lab or "").strip()
    if not lab or not _lab_exists(window.api, lab):
        return False

    window.log(f"REBUILD: existing EVE-NG lab found: {lab}")
    controller = getattr(window, "_active_lab_controller", None)

    if controller is not None:
        controller._close_consoles()
        controller._stop_lab(lab)
    else:
        window.api.stop_all(lab)
        window.log(f"Stopped all EVE nodes before rebuild: {lab}")

    window.log(f"REBUILD: deleting existing lab: {lab}")
    window.api.delete_lab(lab)
    if not _wait_until_deleted(window.api, lab):
        raise RuntimeError(
            f"EVE-NG accepted deletion of {lab}, but the lab still exists after waiting. "
            "Rebuild was aborted."
        )

    if controller is not None:
        controller.clear_if_active(lab)

    workspace = getattr(window, "_console_workspace", None)
    override = getattr(workspace, "_eve_lab_override", None) if workspace else None
    if override is not None:
        try:
            if str(override.get() or "").strip() == lab:
                override.set("AUTO — resolve from active topology")
        except Exception:
            pass

    window.log(f"REBUILD: old lab destroyed successfully: {lab}")
    return True


def _replace_enabled(window):
    variable = getattr(window, "replace_existing_lab", None)
    if variable is None:
        return True
    try:
        return bool(variable.get())
    except Exception:
        return True


def _prepare_rebuild(window, lab):
    if not _replace_enabled(window):
        return False
    return _destroy_existing_lab(window, lab)


def _install_rebuild_ui(window):
    saved = window.settings.data.setdefault("lab", {}).get("replace_existing", True)
    window.replace_existing_lab = tk.BooleanVar(value=bool(saved))

    def persist(*_args):
        window.settings.data.setdefault("lab", {})["replace_existing"] = bool(
            window.replace_existing_lab.get()
        )
        window.settings.save()

    window.replace_existing_lab.trace_add("write", persist)

    for page, label in (
        (window.t_master, "Master Lab rebuild policy"),
        (window.t_labs, "Training Lab rebuild policy"),
    ):
        row = tk.Frame(
            page,
            bg=window.SURFACE,
            highlightbackground=window.BORDER,
            highlightthickness=1,
        )
        row.pack(fill="x", pady=(10, 0))
        tk.Label(
            row,
            text=label.upper(),
            bg=window.SURFACE,
            fg=window.MUTED,
            font=(window.font_family, 8, "bold"),
        ).pack(side="left", padx=(14, 10), pady=10)
        ttk.Checkbutton(
            row,
            text="Replace existing lab automatically (stop → close consoles → delete → rebuild)",
            variable=window.replace_existing_lab,
        ).pack(side="left", pady=8)


def _install_rebuild_wrappers(window):
    original_build_master = window.build_master
    original_create_scenario = window.create_scenario_lab

    def build_master(self):
        target = self.current_lab_path()
        _prepare_rebuild(self, target)
        return original_build_master()

    build_master.__name__ = "build_master"

    def create_scenario_lab(self):
        if not self.current_scenario:
            raise RuntimeError("Select a scenario first.")
        target = self._scenario_lab_path(self.current_scenario)
        _prepare_rebuild(self, target)
        return original_create_scenario()

    create_scenario_lab.__name__ = "create_scenario_lab"

    window.build_master = types.MethodType(build_master, window)
    window.create_scenario_lab = types.MethodType(create_scenario_lab, window)


def _pre_recovery_backend(current):
    """Find the exact-runtime resolver that existed before 4.5.1 recovery wrapping."""
    if not getattr(current, "_stale_runtime_recovery", False):
        return current
    try:
        original = inspect.getclosurevars(current).nonlocals.get("original")
    except Exception:
        original = None
    return original if callable(original) else current


def _interactive_backend(base, recovered, validator, lab, node_id, node_info, attempts, delay):
    """Try the stable console path first; only recycle a node after a real failure."""
    first_attempts = min(max(int(attempts), 1), 6)
    first_delay = min(max(float(delay), 0.1), 0.5)
    try:
        return base(
            validator,
            lab,
            node_id,
            node_info=node_info,
            attempts=first_attempts,
            delay=first_delay,
        )
    except RuntimeError as exc:
        if "No exact console backend available" not in str(exc):
            raise
        validator.log(
            f"Node {node_id}: interactive console normal runtime lookup failed; "
            "trying controlled recovery once."
        )
        return recovered(
            validator,
            lab,
            node_id,
            node_info=node_info,
            attempts=attempts,
            delay=delay,
        )


def _install_console_recovery_isolation():
    current = LiveValidator._console_backend
    if getattr(current, "_interactive_console_isolated", False):
        return

    base = _pre_recovery_backend(current)
    recovered = current

    def routed(self, lab, node_id, node_info=None, attempts=15, delay=1.0):
        if getattr(_INTERACTIVE_CONSOLE, "active", False):
            return _interactive_backend(
                base,
                recovered,
                self,
                lab,
                node_id,
                node_info,
                attempts,
                delay,
            )
        return recovered(
            self,
            lab,
            node_id,
            node_info=node_info,
            attempts=attempts,
            delay=delay,
        )

    routed._interactive_console_isolated = True
    LiveValidator._console_backend = routed

    original_worker = TerminalSessionView._connect_worker
    if getattr(original_worker, "_interactive_console_context", False):
        return

    def console_worker(self):
        previous = getattr(_INTERACTIVE_CONSOLE, "active", False)
        _INTERACTIVE_CONSOLE.active = True
        try:
            return original_worker(self)
        finally:
            _INTERACTIVE_CONSOLE.active = previous

    console_worker._interactive_console_context = True
    TerminalSessionView._connect_worker = console_worker


def install_lab_rebuild_and_console_fix(window):
    """Install safe replace/rebuild generation and restore interactive console behavior."""
    if getattr(window, "_lab_rebuild_console_fix_installed", False):
        return window

    _install_delete_lab_api()
    _install_console_recovery_isolation()
    _install_rebuild_ui(window)
    _install_rebuild_wrappers(window)

    window._lab_rebuild_console_fix_installed = True
    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except Exception:
        pass
    return window
