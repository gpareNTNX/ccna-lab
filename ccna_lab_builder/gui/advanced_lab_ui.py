"""UI polish for the combined Cisco Challenge and Advanced lab workspace."""

import tkinter as tk
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


def _widget_text(widget):
    """Return a widget text option when it exists, otherwise None.

    Tk 9 raises TclError when ``cget('text')`` is called on containers such as
    ``Frame``. The challenge page contains a mix of labels and containers, so
    label discovery must treat missing text options as normal rather than as a
    startup failure.
    """
    try:
        options = widget.keys()
        if "text" not in options:
            return None
        return str(widget.cget("text"))
    except (AttributeError, TypeError, tk.TclError):
        return None


def _rename_page_labels(window):
    page = getattr(window, "t_challenges", None)
    if page is None:
        return

    for container in page.winfo_children():
        for child in container.winfo_children():
            text = _widget_text(child)
            if text == "Cisco Challenge Labs":
                child.configure(text=PAGE_TITLE)
            elif text and "Converted EVE-NG challenges only" in text:
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
