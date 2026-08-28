"""Single-active-lab coordination for EVE-NG workspaces."""

from __future__ import annotations

import threading
import types
import tkinter as tk
from tkinter import ttk

from ccna_lab_builder.gui.console_lab_discovery import _discover_via_ssh


VERSION = "4.5.0"


def _normalize_lab(value):
    text = str(value or "").strip()
    if not text:
        return ""
    return text if text.startswith("/") else "/" + text


class SingleActiveLabController:
    """Guarantee that only one EVE-NG lab is active from this application."""

    def __init__(self, window, workspace):
        self.window = window
        self.workspace = workspace
        self.active_lab = ""
        self._initialized = False
        self._lock = threading.RLock()
        self._status_label = None
        self._state_label = None

    def bind_status_widgets(self, status_label, state_label):
        self._status_label = status_label
        self._state_label = state_label
        self._publish_status("NO ACTIVE LAB", "IDLE", self.window.MUTED)

    def _ui(self, func):
        try:
            if threading.current_thread() is threading.main_thread():
                func()
            else:
                self.window.after(0, func)
        except Exception:
            pass

    def _publish_status(self, lab, state, color):
        def apply():
            if self._status_label is not None:
                self._status_label.configure(text=lab or "NO ACTIVE LAB")
            if self._state_label is not None:
                self._state_label.configure(text=f"● {state}", fg=color)

        self._ui(apply)

    def _close_consoles(self):
        workspace = self.workspace
        self.window.log("Closing all interactive device consoles before lab transition...")

        def close_tabs():
            try:
                workspace.disconnect_all()
            except Exception as exc:
                self.window.log(f"WARNING: console disconnect: {exc}")

            notebook = getattr(workspace, "notebook", None)
            sessions = getattr(workspace, "sessions", None)
            if notebook is None or not isinstance(sessions, dict):
                return
            for view in list(sessions.values()):
                try:
                    notebook.forget(view)
                except Exception:
                    pass
                try:
                    view.destroy()
                except Exception:
                    pass
            sessions.clear()

        if threading.current_thread() is threading.main_thread():
            close_tabs()
            return

        done = threading.Event()

        def wrapped():
            try:
                close_tabs()
            finally:
                done.set()

        self.window.after(0, wrapped)
        if not done.wait(5):
            raise RuntimeError("Timed out while closing interactive console tabs.")

    def _discover_labs(self):
        try:
            return list(_discover_via_ssh(self.workspace))
        except Exception as exc:
            self.window.log(f"WARNING: global EVE lab discovery failed: {exc}")
            return []

    @staticmethod
    def _is_missing_lab_error(exc):
        text = str(exc).lower()
        return "does not exist" in text or "60000" in text or "404" in text

    def _stop_lab(self, lab):
        lab = _normalize_lab(lab)
        if not lab:
            return
        try:
            self.window.api.stop_all(lab)
            self.window.log(f"Stopped all EVE nodes: {lab}")
        except RuntimeError as exc:
            if self._is_missing_lab_error(exc):
                self.window.log(f"Lab no longer exists, skipping stop: {lab}")
                return
            raise RuntimeError(f"Could not stop active EVE lab {lab}: {exc}") from exc

    def _labs_to_stop(self, target):
        target = _normalize_lab(target)
        ordered = []
        current = _normalize_lab(self.active_lab)
        if current and current != target:
            ordered.append(current)

        # The first activation after app launch also catches labs left running by
        # EVE-NG or a previous application session. Later swaps only need to stop
        # the tracked active lab, keeping transitions fast.
        if not self._initialized:
            for lab in self._discover_labs():
                lab = _normalize_lab(lab)
                if lab and lab != target and lab not in ordered:
                    ordered.append(lab)
        return ordered

    def switch_to(self, target, reason="Switching lab"):
        target = _normalize_lab(target)
        if not target:
            raise RuntimeError("Cannot switch EVE-NG lab: target path is empty.")
        if not self.window.api or not self.window.ssh:
            raise RuntimeError("Connect to EVE-NG SSH + API first.")

        with self._lock:
            if self._initialized and _normalize_lab(self.active_lab) == target:
                self._publish_status(target, "ACTIVE", self.window.SUCCESS)
                return target

            previous = _normalize_lab(self.active_lab)
            self.window.log(f"{reason}: preparing EVE-NG lab transition to {target}")
            self._publish_status(target, "SWITCHING", self.window.ACCENT)

            try:
                self._close_consoles()
                labs = self._labs_to_stop(target)
                if labs:
                    self.window.log(
                        f"Single Active Lab: stopping {len(labs)} other EVE lab(s) "
                        "before activation..."
                    )
                for lab in labs:
                    self._stop_lab(lab)
            except Exception:
                self._publish_status(
                    previous or "NO ACTIVE LAB", "SWITCH FAILED", self.window.DANGER
                )
                self.window.log(
                    f"Lab transition aborted; target was not activated: {target}"
                )
                raise

            if previous and previous != target:
                self.window.log(f"Previous EVE lab closed: {previous}")
            elif not self._initialized:
                self.window.log("Initial EVE lab safety sweep complete.")

            self.active_lab = target
            self._initialized = True
            self._publish_status(target, "ACTIVE", self.window.SUCCESS)
            self.window.log(f"Active EVE lab: {target}")
            return target

    def mark_active(self, lab):
        lab = _normalize_lab(lab)
        if not lab:
            return
        with self._lock:
            self.active_lab = lab
            self._initialized = True
            self._publish_status(lab, "ACTIVE", self.window.SUCCESS)

    def clear_if_active(self, lab):
        lab = _normalize_lab(lab)
        with self._lock:
            if lab and _normalize_lab(self.active_lab) == lab:
                self.active_lab = ""
                self._publish_status("NO ACTIVE LAB", "IDLE", self.window.MUTED)

    def stop_and_close_active(self):
        if not self.window.api:
            raise RuntimeError("Connect to EVE-NG first.")

        with self._lock:
            current = _normalize_lab(self.active_lab)
            self._publish_status(current or "ACTIVE LAB", "CLOSING", self.window.WARNING)
            self._close_consoles()
            if current:
                self._stop_lab(current)
                self.window.log(f"Active EVE lab closed: {current}")
            else:
                # If the app has no tracked active lab, still leave EVE in a known
                # idle state by stopping every discovered lab.
                for lab in self._discover_labs():
                    self._stop_lab(lab)
                self.window.log("No tracked active lab; completed global EVE stop sweep.")

            self.active_lab = ""
            self._initialized = True
            self._publish_status("NO ACTIVE LAB", "IDLE", self.window.MUTED)


def _install_console_status_ui(window, workspace, controller):
    row = tk.Frame(window.t_console, bg=window.SURFACE)
    row.pack(fill="x", pady=(0, 8), before=workspace.notebook)

    tk.Label(
        row,
        text="ACTIVE LAB",
        bg=window.SURFACE,
        fg=window.MUTED,
        font=(window.font_family, 8, "bold"),
    ).pack(side="left", padx=(12, 8), pady=9)

    status = tk.Label(
        row,
        text="NO ACTIVE LAB",
        bg=window.SURFACE,
        fg=window.TEXT,
        anchor="w",
        font=(window.mono_family, 8),
    )
    status.pack(side="left", fill="x", expand=True, pady=9)

    state = tk.Label(
        row,
        text="● IDLE",
        bg=window.SURFACE,
        fg=window.MUTED,
        font=(window.font_family, 8, "bold"),
    )
    state.pack(side="left", padx=10)

    ttk.Button(
        row,
        text="STOP & CLOSE ACTIVE LAB",
        command=lambda: window.bg(controller.stop_and_close_active),
    ).pack(side="right", padx=(0, 12), pady=6)

    controller.bind_status_widgets(status, state)


def _install_method_wrappers(window, workspace, controller):
    original_build_master = window.build_master
    original_create_scenario = window.create_scenario_lab
    original_lab_action = window.lab_action
    original_validate_live = window.validate_live
    original_open_device = workspace.open_device

    def build_master(self):
        target = self.current_lab_path()
        controller.switch_to(target, "Building Master Lab")
        lab = original_build_master()
        controller.mark_active(lab or target)
        return lab

    build_master.__name__ = "build_master"

    def create_scenario_lab(self):
        if not self.current_scenario:
            raise RuntimeError("Select a scenario first.")
        target = self._scenario_lab_path(self.current_scenario)
        controller.switch_to(
            target,
            f"Opening Training Lab {self.current_scenario.get('id', '?')}",
        )
        lab = original_create_scenario()
        controller.mark_active(lab or target)
        return lab

    create_scenario_lab.__name__ = "create_scenario_lab"

    def lab_action(self, action):
        target = self.current_lab_path()
        if action == "start":
            controller.switch_to(target, "Starting Master Lab")
        result = original_lab_action(action)
        if action == "start":
            controller.mark_active(target)
        elif action == "stop":
            controller.clear_if_active(target)
        return result

    def validate_live(self):
        target = _normalize_lab(self.validation_lab.get())
        if not target:
            raise RuntimeError("Select a validation target first.")
        controller.switch_to(target, "Starting Live Validator")
        controller.mark_active(target)
        return original_validate_live()

    validate_live.__name__ = "validate_live"

    def open_device(self, node_name):
        # Resolve the real .unl path first. A console double-click therefore becomes
        # a genuine lab activation/swap operation instead of silently opening a
        # second lab behind the active one.
        def worker():
            try:
                target = self.resolve_existing_lab(node_name)
                controller.switch_to(target, f"Opening {node_name} console")
                window.after(0, lambda: original_open_device(node_name))
            except Exception as exc:
                message = str(exc)
                window.log("ERROR: lab swap before console: " + message)

                def failed():
                    from tkinter import messagebox

                    messagebox.showerror("Device Console", message)

                window.after(0, failed)

        threading.Thread(target=worker, daemon=True).start()

    window.build_master = types.MethodType(build_master, window)
    window.create_scenario_lab = types.MethodType(create_scenario_lab, window)
    window.lab_action = types.MethodType(lab_action, window)
    window.validate_live = types.MethodType(validate_live, window)
    workspace.open_device = types.MethodType(open_device, workspace)
    window.open_device_console = workspace.open_device


def install_single_active_lab(window):
    """Install automatic stop/close behavior before every EVE-NG lab swap."""
    if getattr(window, "_single_active_lab_installed", False):
        return getattr(window, "_active_lab_controller", None)

    workspace = getattr(window, "_console_workspace", None)
    if workspace is None:
        return None

    controller = SingleActiveLabController(window, workspace)
    window._active_lab_controller = controller
    window.stop_and_close_active_lab = controller.stop_and_close_active

    _install_console_status_ui(window, workspace, controller)
    _install_method_wrappers(window, workspace, controller)

    window._single_active_lab_installed = True
    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except Exception:
        pass
    return controller
