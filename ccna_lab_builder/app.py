import re
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.core.console_auth import (
    LAB_ENABLE_SECRET,
    LAB_IOS_PASSWORD,
    LAB_IOS_USERNAME,
)
from ccna_lab_builder.gui.main import MainWindow


class SafeMainWindow(MainWindow):
    """Main window with thread-safe errors, validation targets and task activity UI."""

    TRACKED_PAGES = {"images", "master", "labs", "validator"}

    def __init__(self, parent):
        self._activity = {}
        self._activity_lines = {}
        self._activity_running = {}
        self._task_context = threading.local()
        super().__init__(parent)
        self._install_activity_panels()

    def _install_activity_panels(self):
        style = ttk.Style(self)
        style.configure(
            "Activity.Horizontal.TProgressbar",
            troughcolor=self.INPUT,
            background=self.ACCENT,
            bordercolor=self.BORDER,
            lightcolor=self.ACCENT,
            darkcolor=self.ACCENT,
        )

        panels = (
            ("images", self.t_images, "Image task activity"),
            ("master", self.t_master, "Master Lab activity"),
            ("labs", self.t_labs, "Scenario creation activity"),
            ("validator", self.t_validate, "Validation activity"),
        )
        for key, page, title in panels:
            self._create_activity_panel(page, key, title)

    def _create_activity_panel(self, page, key, title):
        outer = tk.Frame(
            page,
            bg=self.SURFACE,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        outer.pack(side="bottom", fill="x", pady=(12, 0))

        header = tk.Frame(outer, bg=self.SURFACE)
        header.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(
            header,
            text=title.upper(),
            bg=self.SURFACE,
            fg=self.MUTED,
            font=(self.font_family, 8, "bold"),
        ).pack(side="left")

        status = tk.Label(
            header,
            text="● IDLE",
            bg=self.SURFACE,
            fg=self.MUTED,
            font=(self.font_family, 8, "bold"),
        )
        status.pack(side="right")

        detail = tk.Label(
            outer,
            text="No task is currently running.",
            bg=self.SURFACE,
            fg=self.TEXT,
            anchor="w",
            justify="left",
            font=(self.font_family, 9),
        )
        detail.pack(fill="x", padx=16)

        progress = ttk.Progressbar(
            outer,
            mode="indeterminate",
            style="Activity.Horizontal.TProgressbar",
        )
        progress.pack(fill="x", padx=16, pady=(8, 8))

        summary = tk.Text(
            outer,
            height=4,
            state="disabled",
            bg=self.INPUT,
            fg="#CBD5E1",
            insertbackground=self.TEXT,
            selectbackground=self.ACCENT_DARK,
            relief="flat",
            bd=0,
            padx=10,
            pady=7,
            wrap="word",
            font=(self.mono_family, 8),
        )
        summary.pack(fill="x", padx=16, pady=(0, 8))

        footer = tk.Frame(outer, bg=self.SURFACE)
        footer.pack(fill="x", padx=16, pady=(0, 10))
        tk.Label(
            footer,
            text="Shows the latest messages from this task. Full history is available in Logs.",
            bg=self.SURFACE,
            fg=self.MUTED,
            font=(self.font_family, 8),
        ).pack(side="left")
        tk.Button(
            footer,
            text="OPEN LOGS",
            command=lambda: self.show_page("logs"),
            relief="flat",
            bd=0,
            highlightthickness=0,
            bg=self.SURFACE_ALT,
            fg=self.TEXT,
            activebackground="#1E293B",
            activeforeground=self.TEXT,
            font=(self.font_family, 8, "bold"),
            padx=10,
            pady=5,
            cursor="hand2",
        ).pack(side="right")

        self._activity[key] = {
            "status": status,
            "detail": detail,
            "progress": progress,
            "summary": summary,
        }
        self._activity_lines[key] = []
        self._activity_running[key] = 0

    def _activity_start(self, key, label):
        activity = self._activity.get(key)
        if not activity:
            return

        self._activity_running[key] = self._activity_running.get(key, 0) + 1
        if self._activity_running[key] == 1:
            self._activity_lines[key] = []
            activity["summary"].configure(state="normal")
            activity["summary"].delete("1.0", "end")
            activity["summary"].configure(state="disabled")
            activity["progress"].start(12)

        activity["status"].configure(text="● RUNNING", fg=self.ACCENT)
        activity["detail"].configure(text=label)
        self._activity_append(key, f"Started: {label}")

    def _activity_append(self, key, message):
        activity = self._activity.get(key)
        if not activity:
            return

        text = str(message).strip()
        if not text:
            return

        lines = self._activity_lines.setdefault(key, [])
        lines.append(text)
        del lines[:-5]

        summary = activity["summary"]
        summary.configure(state="normal")
        summary.delete("1.0", "end")
        summary.insert("1.0", "\n".join(lines))
        summary.see("end")
        summary.configure(state="disabled")

    def _activity_finish(self, key, succeeded, detail=""):
        activity = self._activity.get(key)
        if not activity:
            return

        running = max(0, self._activity_running.get(key, 1) - 1)
        self._activity_running[key] = running
        if running:
            return

        activity["progress"].stop()
        if succeeded:
            activity["status"].configure(text="● COMPLETE", fg=self.SUCCESS)
            activity["detail"].configure(text=detail or "Task completed successfully.")
            self._activity_append(key, "Task completed successfully.")
        else:
            activity["status"].configure(text="● FAILED", fg=self.DANGER)
            activity["detail"].configure(text=detail or "Task failed.")
            self._activity_append(key, "Task failed. See the latest message above.")

    def _task_label(self, key, func):
        name = getattr(func, "__name__", "")
        labels = {
            "install_images": "Installing selected IOS images on EVE-NG…",
            "scan_images": "Scanning the EVE-NG image inventory…",
            "build_master": "Building the Master Lab topology…",
            "create_scenario_lab": "Creating a fresh scenario lab…",
            "validate_live": "Running live validation against IOS consoles…",
        }
        if name in labels:
            return labels[name]
        defaults = {
            "images": "Running IOS image operation…",
            "master": "Running Master Lab operation…",
            "labs": "Running Training Lab operation…",
            "validator": "Running Validator operation…",
        }
        return defaults.get(key, "Running task…")

    def log(self, message):
        super().log(message)
        key = getattr(self._task_context, "key", None)
        if key in self._activity:
            payload = str(message)
            self.after(
                0,
                lambda task_key=key, text=payload: self._activity_append(
                    task_key, text
                ),
            )

    def bg(self, func):
        key = self._current_page if self._current_page in self.TRACKED_PAGES else None
        if not key or key not in self._activity:
            return super().bg(func)

        label = self._task_label(key, func)
        threading.Thread(
            target=self._run_tracked_task,
            args=(func, key, label),
            daemon=True,
        ).start()

    def _run_tracked_task(self, func, key, label):
        self._task_context.key = key
        self.after(
            0,
            lambda task_key=key, task_label=label: self._activity_start(
                task_key, task_label
            ),
        )
        try:
            func()
        except Exception as exc:
            message = str(exc)
            self.log("ERROR: " + message)
            self.after(
                0,
                lambda task_key=key, text=message: self._activity_finish(
                    task_key, False, text
                ),
            )
            self.after(
                0,
                lambda msg=message: messagebox.showerror("CCNA Lab Builder", msg),
            )
        else:
            self.after(
                0,
                lambda task_key=key: self._activity_finish(
                    task_key, True, "Task completed successfully."
                ),
            )
        finally:
            try:
                del self._task_context.key
            except AttributeError:
                pass

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
