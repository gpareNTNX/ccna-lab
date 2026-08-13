import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.core.eve_api import EVEApi
from ccna_lab_builder.core.images import detect_image, install_image
from ccna_lab_builder.core.live_validation import LiveValidator
from ccna_lab_builder.core.scenarios import ScenarioCatalog
from ccna_lab_builder.core.settings import Settings
from ccna_lab_builder.core.ssh import SSHConnection
from ccna_lab_builder.core.validator import Validator


class MainWindow(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.settings = Settings()
        self.ssh = None
        self.api = None
        self.router_image = None
        self.switch_image = None
        self.router_folder = None
        self.switch_folder = None
        self.catalog = ScenarioCatalog()
        self.current_scenario = None
        self._build()

    def _build(self):
        ttk.Label(
            self,
            text="CCNA 200-301 EVE-NG LAB BUILDER",
            font=("Helvetica", 22, "bold"),
        ).pack(pady=(15, 2))
        ttk.Label(
            self,
            text="V4.1 • Existing EVE-NG integration • Scenario engine • Live validation",
        ).pack(pady=(0, 10))
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=18, pady=8)

        self.t_conn = ttk.Frame(self.nb)
        self.t_images = ttk.Frame(self.nb)
        self.t_master = ttk.Frame(self.nb)
        self.t_labs = ttk.Frame(self.nb)
        self.t_validate = ttk.Frame(self.nb)
        for widget, text in [
            (self.t_conn, " EVE-NG "),
            (self.t_images, " IOS IMAGES "),
            (self.t_master, " MASTER LAB "),
            (self.t_labs, " TRAINING LABS "),
            (self.t_validate, " VALIDATOR "),
        ]:
            self.nb.add(widget, text=text)

        self._connection_tab()
        self._images_tab()
        self._master_tab()
        self._labs_tab()
        self._validator_tab()

        self.log_box = tk.Text(self, height=9, state="disabled")
        self.log_box.pack(fill="x", padx=18, pady=(4, 16))

    def log(self, message):
        def append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", str(message) + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

        self.after(0, append)

    def bg(self, func):
        threading.Thread(target=self._safe_run, args=(func,), daemon=True).start()

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
    def field(parent, label, row, value="", secret=False):
        ttk.Label(parent, text=label, width=22).grid(
            row=row, column=0, sticky="w", pady=7
        )
        entry = ttk.Entry(parent, width=52, show="*" if secret else "")
        entry.insert(0, str(value))
        entry.grid(row=row, column=1, padx=10, pady=7)
        return entry

    def _connection_tab(self):
        f = ttk.Frame(self.t_conn, padding=30)
        f.pack(fill="both", expand=True)
        ttk.Label(
            f,
            text=(
                "Connect this desktop application to an existing EVE-NG server. "
                "SSH/CLI and Web/API credentials are separate on a standard EVE-NG installation."
            ),
            wraplength=800,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))
        eve = self.settings.data["eve"]
        self.host = self.field(f, "EVE-NG Host", 1, eve["host"])

        ttk.Label(f, text="SSH / CLI", font=("Helvetica", 12, "bold")).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(12, 2)
        )
        self.ssh_user = self.field(
            f, "SSH Username", 3, eve.get("ssh_username", "root")
        )
        self.ssh_password = self.field(f, "SSH Password", 4, "", True)
        self.ssh_port = self.field(f, "SSH Port", 5, eve["ssh_port"])

        ttk.Label(f, text="EVE Web / API", font=("Helvetica", 12, "bold")).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(16, 2)
        )
        self.api_user = self.field(
            f, "API Username", 7, eve.get("api_username", "admin")
        )
        self.api_password = self.field(f, "API Password", 8, "", True)
        self.https = tk.BooleanVar(value=eve["https"])
        ttk.Checkbutton(
            f,
            text="Use HTTPS API (EVE-NG Pro)",
            variable=self.https,
        ).grid(row=9, column=1, sticky="w")
        ttk.Label(
            f,
            text="Community: normally HTTP. Pro: HTTPS and html5=0 are used for API login.",
        ).grid(row=10, column=1, sticky="w", pady=(4, 0))
        ttk.Button(
            f,
            text="TEST SSH + API",
            command=lambda: self.bg(self.test_connection),
        ).grid(row=11, column=1, sticky="e", pady=18)

    def test_connection(self):
        host = self.host.get().strip()
        if not host:
            raise ValueError("Enter the EVE-NG host.")
        if not self.ssh_user.get().strip():
            raise ValueError("Enter the SSH username.")
        if not self.api_user.get().strip():
            raise ValueError("Enter the EVE Web/API username.")

        self.log("Connecting via SSH...")
        self.ssh = SSHConnection(
            host,
            self.ssh_user.get().strip(),
            self.ssh_password.get(),
            self.ssh_port.get(),
        )
        hostname = self.ssh.connect()
        self.log(f"SSH OK: {hostname}")

        self.log("Connecting to EVE-NG Web/API...")
        self.api = EVEApi(
            host,
            self.api_user.get().strip(),
            self.api_password.get(),
            https=self.https.get(),
        )
        self.api.login()
        self.log("EVE-NG API OK.")

        self.settings.data["eve"].update(
            {
                "host": host,
                "ssh_port": int(self.ssh_port.get()),
                "ssh_username": self.ssh_user.get().strip(),
                "api_username": self.api_user.get().strip(),
                "https": self.https.get(),
            }
        )
        self.settings.save()
        self.after(
            0,
            lambda: messagebox.showinfo(
                "EVE-NG", "SSH + API connection successful."
            ),
        )

    def _images_tab(self):
        f = ttk.Frame(self.t_images, padding=30)
        f.pack(fill="both", expand=True)
        ttk.Label(
            f,
            text="Cisco virtual images",
            font=("Helvetica", 17, "bold"),
        ).pack(anchor="w", pady=(0, 14))
        self.router_label = ttk.Label(f, text="IOSv L3: not selected")
        self.router_label.pack(anchor="w", pady=5)
        ttk.Button(
            f,
            text="SELECT IOSv",
            command=lambda: self.pick_image(False),
        ).pack(anchor="w", pady=5)
        self.switch_label = ttk.Label(f, text="IOSvL2: not selected")
        self.switch_label.pack(anchor="w", pady=(15, 5))
        ttk.Button(
            f,
            text="SELECT IOSvL2",
            command=lambda: self.pick_image(True),
        ).pack(anchor="w", pady=5)
        ttk.Separator(f).pack(fill="x", pady=20)
        ttk.Button(
            f,
            text="INSTALL SELECTED IMAGES",
            command=lambda: self.bg(self.install_images),
        ).pack(anchor="w")
        ttk.Button(
            f,
            text="SCAN INSTALLED IMAGES",
            command=lambda: self.bg(self.scan_images),
        ).pack(anchor="w", pady=10)

    def pick_image(self, l2):
        path = filedialog.askopenfilename(
            filetypes=[
                ("QEMU image", "*.qcow2 *.qcow *.img"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        try:
            info = detect_image(path)
            if l2 and info["template"] != "viosl2":
                raise ValueError("Select an IOSvL2 image.")
            if not l2 and info["template"] != "vios":
                raise ValueError("Select an IOSv L3 image.")
            if l2:
                self.switch_image = (path, info)
                self.switch_label.configure(
                    text=f"IOSvL2: {path}\nEVE folder: {info['folder']}"
                )
            else:
                self.router_image = (path, info)
                self.router_label.configure(
                    text=f"IOSv: {path}\nEVE folder: {info['folder']}"
                )
        except Exception as exc:
            messagebox.showerror("Image", str(exc))

    def install_images(self):
        if not self.ssh:
            raise RuntimeError("Connect to EVE-NG first.")
        if self.router_image:
            self.router_folder = install_image(
                self.ssh,
                self.router_image[0],
                self.router_image[1],
                self.log,
            )
        if self.switch_image:
            self.switch_folder = install_image(
                self.ssh,
                self.switch_image[0],
                self.switch_image[1],
                self.log,
            )
        self.log("Image installation complete.")

    def scan_images(self):
        if not self.ssh:
            raise RuntimeError("Connect to EVE-NG first.")
        images = self.ssh.installed_qemu_images()
        routers = [x for x in images if x.startswith("vios-")]
        switches = [x for x in images if x.startswith("viosl2-")]
        self.log("Installed IOSv: " + (", ".join(routers) or "none"))
        self.log("Installed IOSvL2: " + (", ".join(switches) or "none"))
        if not self.router_folder and routers:
            self.router_folder = routers[-1]
        if not self.switch_folder and switches:
            self.switch_folder = switches[-1]

    def _master_tab(self):
        f = ttk.Frame(self.t_master, padding=30)
        f.pack(fill="both", expand=True)
        lab = self.settings.data["lab"]
        self.folder = self.field(f, "EVE folder", 0, lab["folder"])
        self.master_name = self.field(f, "Master lab name", 1, lab["master_name"])
        self.experimental = tk.BooleanVar(
            value=self.settings.data["compatibility"]["experimental_cabling"]
        )
        ttk.Checkbutton(
            f,
            text="Enable experimental API cabling (version-dependent)",
            variable=self.experimental,
        ).grid(row=2, column=1, sticky="w", pady=8)
        ttk.Button(
            f,
            text="BUILD MASTER LAB",
            command=lambda: self.bg(self.build_master),
        ).grid(row=3, column=1, sticky="e", pady=18)
        ttk.Button(
            f,
            text="START ALL",
            command=lambda: self.bg(lambda: self.lab_action("start")),
        ).grid(row=4, column=1, sticky="e", pady=4)
        ttk.Button(
            f,
            text="STOP ALL",
            command=lambda: self.bg(lambda: self.lab_action("stop")),
        ).grid(row=5, column=1, sticky="e", pady=4)
        ttk.Button(f, text="WIPE ALL", command=self.confirm_wipe).grid(
            row=6, column=1, sticky="e", pady=4
        )

    def _selected_images(self):
        if not self.router_folder and self.router_image:
            self.router_folder = self.router_image[1]["folder"]
        if not self.switch_folder and self.switch_image:
            self.switch_folder = self.switch_image[1]["folder"]
        if not self.router_folder or not self.switch_folder:
            raise RuntimeError("Install or scan an IOSv and IOSvL2 image first.")
        return self.router_folder, self.switch_folder

    def build_master(self):
        if not self.api:
            raise RuntimeError("Connect to EVE-NG first.")
        router_image, switch_image = self._selected_images()
        builder = LabBuilder(self.api, self.log)
        lab = builder.create(
            self.folder.get().strip(),
            self.master_name.get().strip(),
            router_image,
            switch_image,
            cable=self.experimental.get(),
        )
        self.settings.data["lab"].update(
            {
                "folder": self.folder.get().strip(),
                "master_name": self.master_name.get().strip(),
            }
        )
        self.settings.data["compatibility"]["experimental_cabling"] = (
            self.experimental.get()
        )
        self.settings.save()
        self.log("Created: " + lab)

    def current_lab_path(self):
        return self.api.lab_path(
            self.folder.get().strip(), self.master_name.get().strip()
        )

    def lab_action(self, action):
        if not self.api:
            raise RuntimeError("Connect to EVE-NG first.")
        lab = self.current_lab_path()
        getattr(self.api, f"{action}_all")(lab)
        self.log(f"{action.upper()} OK: {lab}")

    def confirm_wipe(self):
        if messagebox.askyesno(
            "Wipe lab",
            "This removes user configuration from all nodes. Continue?",
        ):
            self.bg(lambda: self.lab_action("wipe"))

    def _labs_tab(self):
        outer = ttk.Frame(self.t_labs, padding=22)
        outer.pack(fill="both", expand=True)
        left = ttk.Frame(outer)
        left.pack(side="left", fill="y")
        right = ttk.Frame(outer)
        right.pack(side="left", fill="both", expand=True, padx=(20, 0))
        self.lab_list = tk.Listbox(left, width=34, height=25)
        for scenario in self.catalog.all():
            self.lab_list.insert("end", f"{scenario['id']} - {scenario['name']}")
        self.lab_list.pack(fill="y", expand=True)
        self.lab_list.bind("<<ListboxSelect>>", self.select_scenario)
        self.scenario_title = ttk.Label(
            right,
            text="Select a lab",
            font=("Helvetica", 17, "bold"),
        )
        self.scenario_title.pack(anchor="w")
        self.scenario_meta = ttk.Label(right, text="")
        self.scenario_meta.pack(anchor="w", pady=5)
        self.scenario_text = tk.Text(
            right,
            height=20,
            wrap="word",
            state="disabled",
        )
        self.scenario_text.pack(fill="both", expand=True, pady=10)
        ttk.Button(
            right,
            text="CREATE FRESH SCENARIO LAB",
            command=lambda: self.bg(self.create_scenario_lab),
        ).pack(anchor="e")

    def select_scenario(self, _event=None):
        sel = self.lab_list.curselection()
        if not sel:
            return
        self.current_scenario = self.catalog.all()[sel[0]]
        scenario = self.current_scenario
        self.scenario_title.configure(
            text=f"{scenario['id']} — {scenario['name']}"
        )
        self.scenario_meta.configure(
            text=(
                f"{scenario['domain']} • {scenario['difficulty']} • "
                f"{scenario['minutes']} min"
            )
        )
        body = scenario["objective"] + "\n\nTasks:\n" + "\n".join(
            f"{index + 1}. {task}"
            for index, task in enumerate(scenario["tasks"])
        )
        self.scenario_text.configure(state="normal")
        self.scenario_text.delete("1.0", "end")
        self.scenario_text.insert("1.0", body)
        self.scenario_text.configure(state="disabled")

    @staticmethod
    def _scenario_lab_name(scenario):
        slug = re.sub(r"[^A-Z0-9._-]+", "-", scenario["name"].upper()).strip("-")
        return f"CCNA-{scenario['id']}-{slug}"

    def create_scenario_lab(self):
        if not self.current_scenario:
            raise RuntimeError("Select a scenario first.")
        if not self.api:
            raise RuntimeError("Connect to EVE-NG first.")
        router_image, switch_image = self._selected_images()
        scenario = self.current_scenario
        name = self._scenario_lab_name(scenario)
        lab = LabBuilder(self.api, self.log).create(
            self.folder.get().strip(),
            name,
            router_image,
            switch_image,
            cable=self.experimental.get(),
        )
        self.log("Scenario lab created: " + lab)

        def select_validation_lab():
            self.validation_lab.delete(0, "end")
            self.validation_lab.insert(0, lab)

        self.after(0, select_validation_lab)

    def _validator_tab(self):
        f = ttk.Frame(self.t_validate, padding=22)
        f.pack(fill="both", expand=True)
        ttk.Label(
            f,
            text="Live validator",
            font=("Helvetica", 17, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            f,
            text=(
                "Validates the currently selected scenario. Required nodes are started "
                "automatically when needed, and IOS output is read until the device prompt returns."
            ),
            wraplength=950,
        ).pack(anchor="w", pady=(4, 10))
        self.validation_lab = ttk.Entry(f, width=80)
        self.validation_lab.insert(0, "/CCNA-200-301/CCNA-MASTER-LAB.unl")
        self.validation_lab.pack(anchor="w", pady=5)
        buttons = ttk.Frame(f)
        buttons.pack(anchor="w", pady=8)
        ttk.Button(
            buttons,
            text="VALIDATE LIVE",
            command=lambda: self.bg(self.validate_live),
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="CLEAR",
            command=lambda: self.validation_output.delete("1.0", "end"),
        ).pack(side="left", padx=8)
        self.validation_output = tk.Text(f, height=24, wrap="word")
        self.validation_output.pack(fill="both", expand=True)

    @staticmethod
    def _format_observed_output(output, max_lines=20):
        lines = [line for line in str(output or "").splitlines() if line.strip()]
        if not lines:
            return ["    <no command output received>"]
        visible = lines[:max_lines]
        rendered = ["    " + line for line in visible]
        if len(lines) > max_lines:
            rendered.append(f"    ... ({len(lines) - max_lines} more lines)")
        return rendered

    def validate_live(self):
        if not self.current_scenario:
            raise RuntimeError("Select a scenario in Training Labs first.")
        if not self.api or not self.ssh:
            raise RuntimeError("Connect to EVE-NG first.")
        results = LiveValidator(self.api, self.ssh, self.log).validate(
            self.validation_lab.get().strip(),
            self.current_scenario,
        )
        score = Validator.score(results)
        text = [f"Score: {score}%", ""]
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            text.append(f"{status} | {result.node} | {result.command}")
            text.append("  Expected: " + ", ".join(result.expected))
            if result.matched:
                text.append("  Matched: " + ", ".join(result.matched))
            if result.missing:
                text.append("  Missing: " + ", ".join(result.missing))
            text.append("  Observed output:")
            text.extend(self._format_observed_output(result.output))
            if result.remediation:
                text.append("  Suggested commands:")
                text.extend("    " + command for command in result.remediation)
            text.append("")

        payload = "\n".join(text)

        def render():
            self.validation_output.delete("1.0", "end")
            self.validation_output.insert("1.0", payload)

        self.after(0, render)
