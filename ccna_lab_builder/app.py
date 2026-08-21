import re
import tkinter as tk
from tkinter import messagebox

from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.core.console_auth import (
    LAB_ENABLE_SECRET,
    LAB_IOS_PASSWORD,
    LAB_IOS_USERNAME,
)
from ccna_lab_builder.gui.main import MainWindow


class SafeMainWindow(MainWindow):
    """Main window with thread-safe errors and explicit validation targets."""

    def _safe_run(self, func):
        try:
            func()
        except Exception as exc:
            message = str(exc)
            self.log("ERROR: " + message)
            self.after(
                0,
                lambda msg=message: messagebox.showerror("CCNA Lab Builder", msg),
            )

    @staticmethod
    def _scenario_lab_name(scenario):
        slug = re.sub(r"[^A-Z0-9]+", "-", scenario["name"].upper()).strip("-")
        return f"CCNA-{scenario['id']}-{slug}"

    def _scenario_lab_path(self, scenario):
        folder = self.folder.get().strip() or "/"
        if not folder.startswith("/"):
            folder = "/" + folder
        prefix = folder.rstrip("/")
        return f"{prefix}/{self._scenario_lab_name(scenario)}.unl"

    def _set_validation_target(self, lab):
        def update():
            self.validation_lab.delete(0, "end")
            self.validation_lab.insert(0, lab)

        self.after(0, update)

    def _append_lab_access_instructions(self, scenario):
        topology = scenario.get("topology") or {}
        nodes = topology.get("nodes", [])
        links = topology.get("links", [])
        access = (
            "\n\nLAB ACCESS CREDENTIALS — use these exact training values\n"
            f"IOS username: {LAB_IOS_USERNAME}\n"
            f"IOS password: {LAB_IOS_PASSWORD}\n"
            f"Enable secret: {LAB_ENABLE_SECRET}\n"
            "These credentials are intentionally shared for this isolated CCNA lab only. "
            "Do not reuse them on production systems.\n"
        )
        if topology:
            access += (
                "\nSCENARIO V2 TOPOLOGY\n"
                f"Nodes: {len(nodes)}\n"
                f"Links: {len(links)}\n"
            )
            if links:
                access += (
                    "Automatic links require 'Enable experimental API cabling'. "
                    "If disabled, build the listed links manually in EVE-NG.\n"
                )
        if scenario.get("id") == "01":
            access += (
                "\nRequired management values for Scenario 01:\n"
                "- Hostname: R1-EDGE\n"
                "- Local user: admin, privilege 15\n"
                "- Domain name: ccna.lab\n"
                "- SSH version: 2\n"
                "- Console: login local\n"
                "- VTY 0 4: login local, transport input ssh\n"
            )
        self.scenario_text.configure(state="normal")
        self.scenario_text.insert("end", access)
        self.scenario_text.configure(state="disabled")

    def select_scenario(self, event=None):
        super().select_scenario(event)
        if not self.current_scenario:
            return
        self._append_lab_access_instructions(self.current_scenario)
        lab = self._scenario_lab_path(self.current_scenario)
        self._set_validation_target(lab)
        schema = self.current_scenario.get("schema_version", 1)
        self.log(f"Validator target selected explicitly: {lab} (scenario schema v{schema})")

    def create_scenario_lab(self):
        if not self.current_scenario:
            raise RuntimeError("Select a scenario first.")
        if not self.api:
            raise RuntimeError("Connect to EVE-NG first.")
        router_image, switch_image = self._selected_images()
        scenario = self.current_scenario
        name = self._scenario_lab_name(scenario)
        topology = scenario.get("topology") or {}
        if topology.get("links") and not self.experimental.get():
            self.log(
                "WARNING: this scenario defines links but automatic cabling is disabled. "
                "The lab will be created with the correct node set only."
            )
        lab = LabBuilder(self.api, self.log).create_scenario(
            self.folder.get().strip(),
            name,
            router_image,
            switch_image,
            scenario,
            cable=self.experimental.get(),
        )
        self.log("Scenario lab created: " + lab)
        self.log("Validator target updated to: " + lab)
        self._set_validation_target(lab)


def _install_tk_listbox_compat():
    """Ignore Listbox styling options unsupported by some Tk builds (notably macOS)."""
    original_listbox = tk.Listbox
    if getattr(original_listbox, "_ccna_ui_compat", False):
        return

    class CompatibleListbox(original_listbox):
        _ccna_ui_compat = True

        def __init__(self, master=None, cnf=None, **kw):
            options = dict(cnf or {})
            options.update(kw)
            options.pop("activebackground", None)
            options.pop("activeforeground", None)
            super().__init__(master, options)

    tk.Listbox = CompatibleListbox


def main():
    _install_tk_listbox_compat()
    root = tk.Tk()
    root.title("CCNA 200-301 EVE-NG Lab Builder")
    root.geometry("1440x900")
    root.minsize(1180, 720)
    root.configure(bg=MainWindow.BG)
    SafeMainWindow(root).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
