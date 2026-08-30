"""EVE-NG cabling/runtime stability hardening for v4.6.1."""

from __future__ import annotations

import inspect
import types

from ccna_lab_builder.core.eve_api import EVEApi
from ccna_lab_builder.core.live_validation import LiveValidator


VERSION = "4.6.1"


def _close_lab_method(self):
    """Close the current EVE-NG lab context for the authenticated pod."""
    return self.request("DELETE", "/labs/close")


def _install_close_lab_api():
    if not hasattr(EVEApi, "close_lab"):
        EVEApi.close_lab = _close_lab_method


def _closure_callable(function, name):
    try:
        value = inspect.getclosurevars(function).nonlocals.get(name)
    except Exception:
        return None
    return value if callable(value) else None


def _console_layers(current):
    """Recover the stable base resolver and optional aggressive recovery resolver."""
    if getattr(current, "_interactive_console_isolated", False):
        base = _closure_callable(current, "base")
        recovered = _closure_callable(current, "recovered")
        if base and recovered:
            return base, recovered

    if getattr(current, "_stale_runtime_recovery", False):
        base = _closure_callable(current, "original")
        if base:
            return base, current

    return current, current


def _install_validator_only_runtime_recovery():
    """Keep aggressive QEMU recycle recovery out of the interactive console path."""
    current = LiveValidator._console_backend
    if getattr(current, "_validator_only_recovery", False):
        return

    base, recovered = _console_layers(current)

    def scoped(self, lab, node_id, node_info=None, attempts=15, delay=1.0):
        resolver = (
            recovered
            if getattr(self, "_allow_stale_runtime_recovery", False)
            else base
        )
        return resolver(
            self,
            lab,
            node_id,
            node_info=node_info,
            attempts=attempts,
            delay=delay,
        )

    scoped._validator_only_recovery = True
    scoped._stable_base = base
    scoped._aggressive_recovery = recovered
    LiveValidator._console_backend = scoped

    original_validate = LiveValidator.validate
    if getattr(original_validate, "_scopes_runtime_recovery", False):
        return

    def validate(self, lab, scenario):
        previous = getattr(self, "_allow_stale_runtime_recovery", False)
        self._allow_stale_runtime_recovery = True
        try:
            return original_validate(self, lab, scenario)
        finally:
            self._allow_stale_runtime_recovery = previous

    validate._scopes_runtime_recovery = True
    LiveValidator.validate = validate


def _install_real_lab_close(controller):
    """Close EVE's pod lab context after a lab has been fully stopped."""
    if controller is None:
        return

    current = controller._stop_lab
    if getattr(current, "_eve_context_close", False):
        return

    def stop_and_close(self, lab):
        result = current(lab)
        close_lab = getattr(self.window.api, "close_lab", None)
        if callable(close_lab):
            try:
                close_lab()
                self.window.log("Closed EVE-NG active lab context.")
            except RuntimeError as exc:
                self.window.log(
                    f"WARNING: EVE-NG lab context close was not accepted: {exc}"
                )
        return result

    stop_and_close._eve_context_close = True
    controller._stop_lab = types.MethodType(stop_and_close, controller)


def install_stability_461(window):
    """Install verified console isolation and real EVE lab close semantics."""
    if getattr(window, "_stability_461_installed", False):
        return window

    _install_close_lab_api()
    _install_validator_only_runtime_recovery()
    _install_real_lab_close(getattr(window, "_active_lab_controller", None))

    window._stability_461_installed = True
    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except Exception:
        pass
    return window
