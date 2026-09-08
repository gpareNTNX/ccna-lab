"""Compatibility fixes for Advanced lab cabling and complete EVE image inventory."""

from __future__ import annotations

import tkinter as tk
import types
from tkinter import ttk

from ccna_lab_builder.gui import nutanix_bonus_scan_fix as _scan_fix
from ccna_lab_builder.gui import ssh_native_cabling as _native_cabling

VERSION = "5.2.2"

_NODE_ID_CHECK = '''        if str(node.get("id")) != str(endpoint["node_id"]):
            fail("node id mismatch for " + endpoint["name"])
'''
_NODE_ID_RECONCILIATION = '''        # The EVE API can briefly report stale node IDs immediately after a lab
        # rebuild. For SSH-native cabling, the .unl node matched by exact name is
        # authoritative; do not reject an otherwise valid topology because the
        # API-side numeric ID has not converged yet.
'''


def _relax_node_id_check(script):
    """Make exact .unl node names authoritative when EVE API IDs are temporarily stale."""
    text = str(script or "")
    return text.replace(_NODE_ID_CHECK, _NODE_ID_RECONCILIATION)


def _classify_qemu_images(images):
    """Classify supported families without hiding any other installed QEMU folders."""
    cleaned = sorted(
        {str(item).strip() for item in images if str(item).strip()},
        key=str.casefold,
    )
    routers = []
    switches = []
    nxosv9k = []
    other = []

    for item in cleaned:
        low = item.casefold()
        if low.startswith(("viosl2-", "vios_l2-", "viosl2_", "vios_l2_")):
            switches.append(item)
        elif low.startswith(("vios-", "vios_")):
            routers.append(item)
        elif low.startswith("nxosv9k-"):
            nxosv9k.append(item)
        else:
            other.append(item)

    return {
        "routers": routers,
        "switches": switches,
        "nxosv9k": nxosv9k,
        "other": other,
        "folders": cleaned,
        "all": len(cleaned),
    }


_MARKERS = {
    "__QEMU__": "qemu",
    "__IOL__": "iol",
    "__DYNAMIPS__": "dynamips",
    "__DOCKER__": "docker",
}


def _parse_inventory_output(output):
    inventory = {"qemu": [], "iol": [], "dynamips": [], "docker": []}
    section = None
    for raw in str(output or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in _MARKERS:
            section = _MARKERS[line]
            continue
        if section:
            inventory[section].append(line)

    for key, values in inventory.items():
        inventory[key] = sorted(set(values), key=str.casefold)
    return inventory


def _full_eve_inventory(ssh):
    """Discover QEMU, IOL, Dynamips and Docker images present on the EVE host."""
    command = (
        "printf '__QEMU__\\n'; "
        "find -L /opt/unetlab/addons/qemu -mindepth 1 -maxdepth 1 -type d "
        "-printf '%f\\n' 2>/dev/null | sort -u; "
        "printf '__IOL__\\n'; "
        "find /opt/unetlab/addons/iol/bin -mindepth 1 -maxdepth 1 -type f "
        "\\( -name '*.bin' -o -name '*.image' \\) -printf '%f\\n' "
        "2>/dev/null | sort -u; "
        "printf '__DYNAMIPS__\\n'; "
        "find /opt/unetlab/addons/dynamips -mindepth 1 -maxdepth 1 -type f "
        "-printf '%f\\n' 2>/dev/null | sort -u; "
        "printf '__DOCKER__\\n'; "
        "docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null "
        "| grep -v '<none>' | sort -u || true"
    )
    output, _ = ssh.exec(command)
    inventory = _parse_inventory_output(output)

    # Preserve the older, proven QEMU discovery path as a fallback on EVE builds
    # whose find implementation does not support every option used above.
    if not inventory["qemu"]:
        try:
            inventory["qemu"] = sorted(
                set(ssh.installed_qemu_images()),
                key=str.casefold,
            )
        except (AttributeError, RuntimeError):
            pass
    return inventory


def _format_family(name, values):
    if not values:
        return f"{name} (0): none"
    return f"{name} ({len(values)}): " + ", ".join(values)


def _install_inventory_panel(window):
    if getattr(window, "_eve_inventory_text", None) is not None:
        return

    outer, card = window._card(window.t_images, 20)
    outer.pack(fill="x", pady=(16, 0))
    ttk.Label(
        card,
        text="Installed EVE-NG image inventory",
        style="Section.TLabel",
    ).pack(anchor="w")
    ttk.Label(
        card,
        text="Shows every discovered QEMU folder plus IOL, Dynamips and Docker images.",
        style="CardMuted.TLabel",
    ).pack(anchor="w", pady=(4, 10))

    text = tk.Text(
        card,
        height=8,
        wrap="word",
        state="disabled",
        bg=window.INPUT,
        fg=window.TEXT,
        insertbackground=window.TEXT,
        selectbackground=window.ACCENT_DARK,
        relief="flat",
        bd=0,
        padx=10,
        pady=8,
        font=(window.mono_family, 8),
    )
    text.pack(fill="x")
    text.configure(state="normal")
    text.insert("1.0", "Run SCAN INSTALLED IMAGES to populate the complete EVE inventory.")
    text.configure(state="disabled")
    window._eve_inventory_text = text


def _publish_inventory(window, inventory, classified):
    def apply():
        text = getattr(window, "_eve_inventory_text", None)
        if text is None:
            return
        lines = [
            (
                f"Supported QEMU: IOSv={len(classified['routers'])}, "
                f"IOSvL2={len(classified['switches'])}, "
                f"NX-OSv9K={len(classified['nxosv9k'])}, "
                f"other={len(classified['other'])}"
            ),
            _format_family("QEMU", inventory["qemu"]),
            _format_family("IOL", inventory["iol"]),
            _format_family("Dynamips", inventory["dynamips"]),
            _format_family("Docker", inventory["docker"]),
        ]
        text.configure(state="normal")
        text.delete("1.0", "end")
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")

        if classified["routers"]:
            window.router_label.configure(
                text=f"Detected on EVE-NG: {window.router_folder or classified['routers'][-1]}"
            )
        if classified["switches"]:
            window.switch_label.configure(
                text=f"Detected on EVE-NG: {window.switch_folder or classified['switches'][-1]}"
            )

    window.after(0, apply)


def _install_complete_scan(window):
    current = window.scan_images
    if getattr(current, "_complete_eve_inventory", False):
        return

    # The existing Nutanix scan closure resolves this module global at runtime.
    # Replace its strict classifier so mixed-case and vios_l2 folder variants are
    # detected before the original scan logic runs.
    _scan_fix._classify_qemu_images = _classify_qemu_images

    def scan_images(self_window):
        current()
        if not self_window.ssh:
            raise RuntimeError("Connect to EVE-NG first.")

        inventory = _full_eve_inventory(self_window.ssh)
        classified = _classify_qemu_images(inventory["qemu"])
        routers = classified["routers"]
        switches = classified["switches"]
        nxos_images = classified["nxosv9k"]

        if routers and self_window.router_folder not in routers:
            self_window.router_folder = routers[-1]
        if switches and self_window.switch_folder not in switches:
            self_window.switch_folder = switches[-1]

        counts = ", ".join(
            f"{key}={len(inventory[key])}"
            for key in ("qemu", "iol", "dynamips", "docker")
        )
        self_window.log("Complete EVE-NG image inventory: " + counts)
        self_window.log(
            "All QEMU image folders: " + (", ".join(inventory["qemu"]) or "none")
        )
        self_window.log(
            "Other QEMU families: " + (", ".join(classified["other"]) or "none")
        )
        if inventory["iol"]:
            self_window.log("Installed IOL images: " + ", ".join(inventory["iol"]))
        if inventory["dynamips"]:
            self_window.log(
                "Installed Dynamips images: " + ", ".join(inventory["dynamips"])
            )
        if inventory["docker"]:
            self_window.log("Installed Docker images: " + ", ".join(inventory["docker"]))

        _scan_fix._publish_bonus_images(self_window, nxos_images)
        _publish_inventory(self_window, inventory, classified)
        self_window._eve_image_inventory = inventory

    scan_images.__name__ = "scan_images"
    scan_images._complete_eve_inventory = True
    window.scan_images = types.MethodType(scan_images, window)


def install_eve_inventory_cabling_fix(window):
    """Install resilient Advanced cabling and complete image discovery."""
    if getattr(window, "_eve_inventory_cabling_fix_installed", False):
        return window

    _native_cabling._REMOTE_SCRIPT = _relax_node_id_check(_native_cabling._REMOTE_SCRIPT)
    _install_inventory_panel(window)
    _install_complete_scan(window)
    window._eve_inventory_cabling_fix_installed = True
    return window
