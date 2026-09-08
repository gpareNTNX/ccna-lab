"""UI polish for the combined Cisco Challenge and Advanced lab workspace."""

import types

from ccna_lab_builder.gui import challenge_pack as _challenge_pack

PAGE_TITLE = "Cisco Challenge + Advanced Labs"
PAGE_SUBTITLE = (
    "Converted challenges + original advanced labs • CCNA labs 01-37 stay unchanged"
)


def _install_pack_aware_topology():
    current = _challenge_pack._render_topology
    if getattr(current, "_advanced_pack_aware", False):
        return

    def render(window, scenario):
        window.topology_canvas.set_topology(
            scenario["topology"],
            title=f"{scenario['id']} — {scenario['name']}",
            subtitle=(
                f"{scenario.get('pack', 'Cisco Challenge')} • "
                f"{scenario['difficulty']} • {scenario['minutes']} min"
            ),
        )
        window._topology_mode = "scenario"

    render._advanced_pack_aware = True
    _challenge_pack._render_topology = render


def _rename_page_labels(window):
    page = getattr(window, "t_challenges", None)
    if page is None:
        return

    for container in page.winfo_children():
        for child in container.winfo_children():
            try:
                text = str(child.cget("text"))
            except (AttributeError, TypeError):
                continue
            if text == "Cisco Challenge Labs":
                child.configure(text=PAGE_TITLE)
            elif "Converted EVE-NG challenges only" in text:
                child.configure(text=PAGE_SUBTITLE)


def install_advanced_lab_ui(window):
    """Make the existing challenge workspace clearly expose the Advanced Cisco pack."""
    if getattr(window, "_advanced_lab_ui_installed", False):
        return window

    _install_pack_aware_topology()
    _rename_page_labels(window)

    nav = getattr(window, "_nav_buttons", {}).get("challenges")
    if nav is not None:
        nav.configure(text="★  Challenge + Advanced")

    original_show_page = window.show_page

    def show_page(self, key):
        result = original_show_page(key)
        if key == "challenges":
            self.page_title.configure(text=PAGE_TITLE)
        return result

    window.show_page = types.MethodType(show_page, window)
    window._advanced_lab_ui_installed = True
    return window
