"""Fix Nutanix Bonus lab selection and expose NX-OSv9K in the global image scan."""

from __future__ import annotations

import types

from ccna_lab_builder.gui.nutanix_bonus import nxosv9k_image_folders


def _classify_qemu_images(images):
    cleaned = sorted({str(item).strip() for item in images if str(item).strip()})
    return {
        "routers": [item for item in cleaned if item.startswith("vios-")],
        "switches": [item for item in cleaned if item.startswith("viosl2-")],
        "nxosv9k": nxosv9k_image_folders(cleaned),
        "all": len(cleaned),
    }


def _select_default_bonus(controller):
    """Select the first Bonus lab only when the user has no existing selection."""
    if controller.current is not None:
        return False
    labs = controller.catalog.all()
    if not labs:
        return False
    controller.listbox.selection_clear(0, "end")
    controller.listbox.selection_set(0)
    controller.listbox.activate(0)
    controller.listbox.see(0)
    controller.select(0)
    return True


def _publish_bonus_images(window, images):
    controller = getattr(window, "_nutanix_bonus_controller", None)
    if controller is None:
        return

    nxos_images = list(images)

    def apply():
        controller.image_combo.configure(values=nxos_images)
        if nxos_images:
            if controller.image_var.get() not in nxos_images:
                controller.image_var.set(nxos_images[-1])
            controller.image_status.configure(
                text=f"✓ {len(nxos_images)} NX-OSv9K image(s) detected on EVE-NG",
                fg=window.SUCCESS,
            )
            controller.create_button.configure(
                state="normal" if controller.current else "disabled"
            )
        else:
            controller.image_var.set("")
            controller.image_status.configure(
                text="No nxosv9k-* image found under /opt/unetlab/addons/qemu.",
                fg=window.DANGER,
            )
            controller.create_button.configure(state="disabled")

    window.after(0, apply)


def _install_global_image_scan(window):
    current = window.scan_images
    if getattr(current, "_nxosv9k_inventory", False):
        return

    def scan_images(self_window):
        if not self_window.ssh:
            raise RuntimeError("Connect to EVE-NG first.")

        inventory = _classify_qemu_images(self_window.ssh.installed_qemu_images())
        routers = inventory["routers"]
        switches = inventory["switches"]
        nxos_images = inventory["nxosv9k"]

        self_window.log(f"Installed QEMU image folders: {inventory['all']} total")
        self_window.log("Installed IOSv: " + (", ".join(routers) or "none"))
        self_window.log("Installed IOSvL2: " + (", ".join(switches) or "none"))
        self_window.log("Installed NX-OSv9K: " + (", ".join(nxos_images) or "none"))

        if not self_window.router_folder and routers:
            self_window.router_folder = routers[-1]
        if not self_window.switch_folder and switches:
            self_window.switch_folder = switches[-1]

        _publish_bonus_images(self_window, nxos_images)

    scan_images.__name__ = "scan_images"
    scan_images._nxosv9k_inventory = True
    window.scan_images = types.MethodType(scan_images, window)


def _install_bonus_auto_selection(window):
    controller = getattr(window, "_nutanix_bonus_controller", None)
    if controller is None or getattr(controller, "_auto_selection_installed", False):
        return

    current_show = controller.show_page

    def show_page():
        _select_default_bonus(controller)
        return current_show()

    controller.show_page = show_page
    controller._auto_selection_installed = True
    window._nav_buttons["nutanix_bonus"].configure(command=show_page)


def install_nutanix_bonus_scan_fix(window):
    _install_global_image_scan(window)
    _install_bonus_auto_selection(window)
    return window
