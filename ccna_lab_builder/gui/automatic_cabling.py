"""Automatic EVE-NG cabling for generated Master and Training labs."""

from __future__ import annotations

import types

from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.core.topology import LINKS


VERSION = "4.4.0"


def _scenario_link_count(scenario):
    topology = (scenario or {}).get("topology") or {}
    if topology:
        return len(topology.get("links", []))
    return len(LINKS)


def _set_automatic_ui(window):
    """Force cabling on and make the old compatibility toggle self-explanatory."""
    try:
        window.experimental.set(True)
    except Exception:
        pass

    def walk(widget):
        try:
            children = widget.winfo_children()
        except Exception:
            return
        for child in children:
            try:
                text = str(child.cget("text"))
            except Exception:
                text = ""
            if "experimental api cabling" in text.lower():
                try:
                    child.configure(
                        text="Automatic API cabling (enabled for generated labs)",
                        state="disabled",
                    )
                except Exception:
                    pass
            walk(child)

    walk(window)


def _build_master(window):
    if not window.api:
        raise RuntimeError("Connect to EVE-NG first.")

    router_image, switch_image = window._selected_images()
    expected_links = len(LINKS)
    window.log(
        f"Automatic cabling enabled: creating {expected_links} Master Lab link(s)..."
    )

    builder = LabBuilder(window.api, window.log)
    lab = builder.create(
        window.folder.get().strip(),
        window.master_name.get().strip(),
        router_image,
        switch_image,
        cable=True,
    )

    window.settings.data["lab"].update(
        {
            "folder": window.folder.get().strip(),
            "master_name": window.master_name.get().strip(),
        }
    )
    window.settings.data["compatibility"]["experimental_cabling"] = True
    window.settings.save()
    try:
        window.experimental.set(True)
    except Exception:
        pass

    window.log(
        f"Created and automatically cabled: {lab} ({expected_links} link(s))."
    )
    return lab


def _create_scenario_lab(window):
    if not window.current_scenario:
        raise RuntimeError("Select a scenario first.")
    if not window.api:
        raise RuntimeError("Connect to EVE-NG first.")

    router_image, switch_image = window._selected_images()
    scenario = window.current_scenario
    name = window._scenario_lab_name(scenario)
    expected_links = _scenario_link_count(scenario)

    if expected_links:
        window.log(
            f"Automatic cabling enabled: creating {expected_links} scenario link(s)..."
        )
    else:
        window.log("Automatic cabling enabled: this scenario defines no links.")

    lab = LabBuilder(window.api, window.log).create_scenario(
        window.folder.get().strip(),
        name,
        router_image,
        switch_image,
        scenario,
        cable=True,
    )

    try:
        window.experimental.set(True)
    except Exception:
        pass
    window.settings.data["compatibility"]["experimental_cabling"] = True
    window.settings.save()

    window.log(
        f"Scenario lab created and automatically cabled: {lab} "
        f"({expected_links} link(s))."
    )
    window.log("Validator target updated to: " + lab)
    window._set_validation_target(lab)
    return lab


def _bound_build_master(self):
    return _build_master(self)


def _bound_create_scenario_lab(self):
    return _create_scenario_lab(self)


_bound_build_master.__name__ = "build_master"
_bound_create_scenario_lab.__name__ = "create_scenario_lab"


def install_automatic_cabling(window):
    """Make all newly generated labs cable their defined topology automatically."""
    if getattr(window, "_automatic_cabling_installed", False):
        return window

    _set_automatic_ui(window)
    window.build_master = types.MethodType(_bound_build_master, window)
    window.create_scenario_lab = types.MethodType(_bound_create_scenario_lab, window)
    window._automatic_cabling_installed = True

    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except Exception:
        pass

    return window
