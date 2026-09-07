"""Manual-only validation policy for the v5 learning experience.

This compatibility layer deliberately disables every automatic validation trigger
introduced by v5.0.0 while preserving power controls, runtime overlays, hints,
and progress history.
"""

from __future__ import annotations

import inspect
import threading
import tkinter as tk
import types

from ccna_lab_builder.gui.console_workspace import TerminalSessionView


VERSION = "5.0.1"


def _cancel_after(window, job):
    if job is None:
        return
    try:
        window.after_cancel(job)
    except (tk.TclError, ValueError):
        pass


def _unwrap_learning_console_hook():
    """Restore the console send method that existed before v5 activity hooks."""
    current = TerminalSessionView._send
    if not getattr(current, "_learning_activity", False):
        return False
    try:
        original = inspect.getclosurevars(current).nonlocals.get("current")
    except Exception:
        return False
    if not callable(original):
        return False
    TerminalSessionView._send = original
    return True


def _clear_validation_widgets(window, controller=None):
    """Clear stale validation presentation before a new manual validation run."""
    output = getattr(window, "validation_output", None)
    if output is not None:
        try:
            output.delete("1.0", "end")
        except tk.TclError:
            pass

    if hasattr(window, "_topology_validation_signature"):
        window._topology_validation_signature = None

    canvas = getattr(window, "topology_canvas", None)
    if canvas is not None:
        try:
            canvas.set_validation({}, None)
        except (AttributeError, tk.TclError):
            pass

    if controller is not None:
        controller._failed_results = []
        controller._failed_index = 0
        coach_target = getattr(controller, "coach_target", None)
        coach_text = getattr(controller, "coach_text", None)
        if coach_target is not None:
            try:
                coach_target.configure(text="Validation in progress…")
            except tk.TclError:
                pass
        if coach_text is not None:
            try:
                coach_text.configure(text="Previous validation results were cleared.")
            except tk.TclError:
                pass


def _clear_before_validation(window, controller=None):
    """Perform the clear on Tk's main thread before validation starts."""
    if threading.current_thread() is threading.main_thread():
        _clear_validation_widgets(window, controller)
        return

    done = threading.Event()

    def apply():
        try:
            _clear_validation_widgets(window, controller)
        finally:
            done.set()

    try:
        window.after(0, apply)
    except tk.TclError:
        return
    done.wait(timeout=2.0)


def install_manual_validation_only(window):
    """Disable continuous validation and make VALIDATE LIVE clear first."""
    if getattr(window, "_manual_validation_only_installed", False):
        return getattr(window, "_learning_controller", None)

    controller = getattr(window, "_learning_controller", None)
    if controller is None:
        return None

    _cancel_after(window, getattr(controller, "_debounce_job", None))
    _cancel_after(window, getattr(controller, "_periodic_job", None))
    controller._debounce_job = None
    controller._periodic_job = None

    continuous_var = getattr(controller, "continuous_var", None)
    if continuous_var is not None:
        try:
            continuous_var.set(False)
        except tk.TclError:
            pass

    learning = window.settings.data.setdefault("learning", {})
    changed = False
    for key in ("continuous_validation", "validation_interval"):
        if key in learning:
            learning.pop(key, None)
            changed = True
    if changed:
        window.settings.save()

    status = getattr(controller, "continuous_status", None)
    if status is not None:
        try:
            status.master.destroy()
        except tk.TclError:
            pass
        try:
            del controller.continuous_status
        except AttributeError:
            pass

    def disabled_schedule(_self, *_args, **_kwargs):
        return None

    def continuous_not_allowed(_self):
        return False

    controller.schedule_validation = types.MethodType(disabled_schedule, controller)
    controller._schedule_periodic_validation = types.MethodType(
        disabled_schedule, controller
    )
    controller._kick_continuous_validation = types.MethodType(
        disabled_schedule, controller
    )
    controller._update_continuous_status = types.MethodType(
        disabled_schedule, controller
    )
    controller._continuous_validation_allowed = types.MethodType(
        continuous_not_allowed, controller
    )

    console_hook_removed = _unwrap_learning_console_hook()

    current_validate_live = window.validate_live

    def validate_live(self_window):
        _clear_before_validation(self_window, controller)
        return current_validate_live()

    validate_live.__name__ = "validate_live"
    window.validate_live = types.MethodType(validate_live, window)
    window._manual_validation_only_installed = True

    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except tk.TclError:
        pass

    detail = "console auto-trigger removed" if console_hook_removed else "manual-only mode active"
    window.log(
        "Validator v5.0.1: continuous validation disabled; "
        f"{detail}; VALIDATE LIVE clears previous results before each run."
    )
    return controller
