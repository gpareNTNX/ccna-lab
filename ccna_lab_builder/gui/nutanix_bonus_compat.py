"""Safety/compatibility layer for the Nutanix NX-OS bonus pack."""

from __future__ import annotations

import threading

from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.core.eve_api import EVEApi

VERSION = "5.1.3"


def _nxos_interface_aliases(value):
    text = str(value or "").strip()
    lower = text.lower()
    suffix = ""
    for prefix in ("ethernet", "eth", "e"):
        if lower.startswith(prefix):
            suffix = text[len(prefix) :]
            break
    if not suffix or not suffix[0].isdigit() or "/" not in suffix:
        return []
    return ["Ethernet" + suffix, "Eth" + suffix, "E" + suffix]


def _install_nxos_interface_aliases():
    """Accept EVE NX-OS interface abbreviations for Cisco Ethernet1/x names."""
    current = LabBuilder._find_interface_index
    if getattr(current, "_nxos_alias_support", False):
        return

    def find_interface(self, lab, node_id, wanted):
        try:
            return current(self, lab, node_id, wanted)
        except RuntimeError:
            for alias in _nxos_interface_aliases(wanted):
                if alias == str(wanted or "").strip():
                    continue
                try:
                    return current(self, lab, node_id, alias)
                except RuntimeError:
                    pass
            raise

    find_interface._nxos_alias_support = True
    LabBuilder._find_interface_index = find_interface


def _install_idempotent_folder_create():
    """Treat EVE 60013 as success so concurrent folder ensure calls are race-safe."""
    current = EVEApi.create_folder
    if getattr(current, "_folder_exists_ok", False):
        return

    def create_folder(self, parent, name):
        try:
            return current(self, parent, name)
        except RuntimeError as exc:
            message = str(exc).lower()
            if "60013" in message or "folder already exists" in message:
                return {
                    "code": 200,
                    "status": "success",
                    "message": "Folder already exists (60013); continuing.",
                }
            raise

    create_folder._folder_exists_ok = True
    EVEApi.create_folder = create_folder


def _install_bonus_build_guard(window):
    """Allow only one Nutanix lab build/rebuild operation per application instance."""
    controller = getattr(window, "_nutanix_bonus_controller", None)
    if controller is None or getattr(controller, "_build_guard_installed", False):
        return

    current = controller.create_lab
    build_lock = threading.Lock()

    def set_button_busy(busy):
        button = getattr(controller, "create_button", None)
        if button is None:
            return
        if busy:
            button.configure(state="disabled")
            return
        enabled = bool(controller.current and str(controller.image_var.get() or "").strip())
        button.configure(state="normal" if enabled else "disabled")

    def create_lab():
        if not build_lock.acquire(blocking=False):
            controller.window.log(
                "Nutanix Bonus build already in progress; duplicate create/rebuild request ignored."
            )
            return None

        controller.window.after(0, lambda: set_button_busy(True))
        try:
            return current()
        finally:
            build_lock.release()
            controller.window.after(0, lambda: set_button_busy(False))

    create_lab._single_build_guard = True
    controller.create_lab = create_lab
    controller._nutanix_build_lock = build_lock
    controller._build_guard_installed = True


def _install_safe_bonus_page(window):
    """Keep all Tk widget mutations on the GUI thread; image scanning stays user-triggered."""
    controller = getattr(window, "_nutanix_bonus_controller", None)
    if controller is None or getattr(controller, "_safe_page_installed", False):
        return

    def show_page():
        w = controller.window
        w.t_nutanix_bonus.tkraise()
        w._current_page = "nutanix_bonus"
        w.page_title.configure(text="Bonus Nutanix")
        for nav_key, button in w._nav_buttons.items():
            button.configure(
                bg=w.SURFACE_ALT if nav_key == "nutanix_bonus" else w.SIDEBAR,
                fg=w.ACCENT if nav_key == "nutanix_bonus" else w.MUTED,
            )

    controller.show_page = show_page
    controller._safe_page_installed = True
    window._nav_buttons["nutanix_bonus"].configure(command=show_page)


def install_nutanix_bonus_compat(window):
    _install_nxos_interface_aliases()
    _install_idempotent_folder_create()
    _install_bonus_build_guard(window)
    _install_safe_bonus_page(window)
    return window
