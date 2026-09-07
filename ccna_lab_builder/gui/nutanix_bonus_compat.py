"""Small safety/compatibility layer for the Nutanix NX-OS bonus pack."""

from __future__ import annotations

from ccna_lab_builder.core.builder import LabBuilder


def _install_nxos_interface_aliases():
    """Accept EVE's Eth1/x abbreviation when a scenario uses Cisco's Ethernet1/x form."""
    current = LabBuilder._find_interface_index
    if getattr(current, "_nxos_alias_support", False):
        return

    def find_interface(self, lab, node_id, wanted):
        try:
            return current(self, lab, node_id, wanted)
        except RuntimeError as original:
            text = str(wanted or "")
            aliases = []
            if text.lower().startswith("ethernet"):
                aliases.append("Eth" + text[len("Ethernet") :])
            elif text.lower().startswith("eth"):
                aliases.append("Ethernet" + text[len("Eth") :])
            for alias in aliases:
                try:
                    return current(self, lab, node_id, alias)
                except RuntimeError:
                    pass
            raise original

    find_interface._nxos_alias_support = True
    LabBuilder._find_interface_index = find_interface


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
    _install_safe_bonus_page(window)
    return window
