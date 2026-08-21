import re
import sys
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
    BG = "#0B0F14"
    SIDEBAR = "#080C11"
    SURFACE = "#111827"
    SURFACE_ALT = "#151E2B"
    INPUT = "#0F172A"
    BORDER = "#263244"
    TEXT = "#E5E7EB"
    MUTED = "#94A3B8"
    ACCENT = "#22D3EE"
    ACCENT_DARK = "#0891B2"
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"

    def __init__(self, parent):
        super().__init__(parent, style="App.TFrame")
        self.settings = Settings()
        self.ssh = None
        self.api = None
        self.router_image = None
        self.switch_image = None
        self.router_folder = None
        self.switch_folder = None
        self.catalog = ScenarioCatalog()
        self.current_scenario = None
        self._nav_buttons = {}
        self._page_titles = {}
        self._current_page = None
        self._configure_styles()
        self._build()

    @staticmethod
    def _font_family():
        if sys.platform == "darwin":
            return "Helvetica Neue"
        if sys.platform.startswith("win"):
            return "Segoe UI"
        return "DejaVu Sans"

    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        family = self._font_family()
        self.font_family = family
        self.mono_family = "Menlo" if sys.platform == "darwin" else "Consolas"

        style.configure("App.TFrame", background=self.BG)
        style.configure("Page.TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.SURFACE)
        style.configure("CardAlt.TFrame", background=self.SURFACE_ALT)
        style.configure("TFrame", background=self.BG)

        style.configure(
            "TLabel",
            background=self.BG,
            foreground=self.TEXT,
            font=(family, 10),
        )
        style.configure(
            "Title.TLabel",
            background=self.BG,
            foreground=self.TEXT,
            font=(family, 24, "bold"),
        )
        style.configure(
            "PageTitle.TLabel",
            background=self.BG,
            foreground=self.TEXT,
            font=(family, 20, "bold"),
        )
        style.configure(
            "Section.TLabel",
            background=self.SURFACE,
            foreground=self.TEXT,
            font=(family, 12, "bold"),
        )
        style.configure(
            "CardTitle.TLabel",
            background=self.SURFACE,
            foreground=self.TEXT,
            font=(family, 11, "bold"),
        )
        style.configure(
            "CardValue.TLabel",
            background=self.SURFACE,
            foreground=self.TEXT,
            font=(family, 20, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background=self.BG,
            foreground=self.MUTED,
            font=(family, 9),
        )
        style.configure(
            "CardMuted.TLabel",
            background=self.SURFACE,
            foreground=self.MUTED,
            font=(family, 9),
        )
        style.configure(
            "Accent.TLabel",
            background=self.BG,
            foreground=self.ACCENT,
            font=(family, 10, "bold"),
        )
        style.configure(
            "Success.TLabel",
            background=self.BG,
            foreground=self.SUCCESS,
            font=(family, 9, "bold"),
        )

        style.configure(
            "TEntry",
            fieldbackground=self.INPUT,
            foreground=self.TEXT,
            insertcolor=self.TEXT,
            bordercolor=self.BORDER,
            lightcolor=self.BORDER,
            darkcolor=self.BORDER,
            padding=(10, 8),
            font=(family, 10),
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", self.ACCENT)],
            lightcolor=[("focus", self.ACCENT)],
            darkcolor=[("focus", self.ACCENT)],
        )

        style.configure(
            "TButton",
            background=self.SURFACE_ALT,
            foreground=self.TEXT,
            bordercolor=self.BORDER,
            focusthickness=0,
            focuscolor=self.SURFACE_ALT,
            padding=(16, 9),
            font=(family, 9, "bold"),
        )
        style.map(
            "TButton",
            background=[("active", "#1E293B"), ("pressed", "#0F172A")],
            foreground=[("disabled", "#64748B")],
        )
        style.configure(
            "Accent.TButton",
            background=self.ACCENT_DARK,
            foreground="#F8FAFC",
            bordercolor=self.ACCENT_DARK,
            focusthickness=0,
            padding=(18, 10),
            font=(family, 9, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#06B6D4"), ("pressed", "#0E7490")],
        )
        style.configure(
            "Danger.TButton",
            background="#7F1D1D",
            foreground="#FEE2E2",
            bordercolor="#991B1B",
            focusthickness=0,
            padding=(16, 9),
            font=(family, 9, "bold"),
        )
        style.map("Danger.TButton", background=[("active", "#991B1B")])

        style.configure(
            "TCheckbutton",
            background=self.SURFACE,
            foreground=self.TEXT,
            font=(family, 10),
        )
        style.map(
            "TCheckbutton",
            background=[("active", self.SURFACE)],
            foreground=[("disabled", self.MUTED)],
        )
        style.configure("TSeparator", background=self.BORDER)

    def _build(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(self, bg=self.SIDEBAR, width=230)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.main_area = ttk.Frame(self, style="App.TFrame")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self._build_sidebar()
        self._build_topbar()

        self.page_host = ttk.Frame(self.main_area, style="Page.TFrame")
        self.page_host.grid(row=1, column=0, sticky="nsew", padx=24, pady=(8, 22))
        self.page_host.grid_rowconfigure(0, weight=1)
        self.page_host.grid_columnconfigure(0, weight=1)

        self.t_dashboard = ttk.Frame(self.page_host, style="Page.TFrame")
        self.t_conn = ttk.Frame(self.page_host, style="Page.TFrame")
        self.t_images = ttk.Frame(self.page_host, style="Page.TFrame")
        self.t_master = ttk.Frame(self.page_host, style="Page.TFrame")
        self.t_labs = ttk.Frame(self.page_host, style="Page.TFrame")
        self.t_validate = ttk.Frame(self.page_host, style="Page.TFrame")
        self.t_logs = ttk.Frame(self.page_host, style="Page.TFrame")

        for page in (
            self.t_dashboard,
            self.t_conn,
            self.t_images,
            self.t_master,
            self.t_labs,
            self.t_validate,
            self.t_logs,
        ):
            page.grid(row=0, column=0, sticky="nsew")

        self._dashboard_tab()
        self._connection_tab()
        self._images_tab()
        self._master_tab()
        self._labs_tab()
        self._validator_tab()
        self._logs_tab()
        self.show_page("dashboard")

    def _build_sidebar(self):
        brand = tk.Frame(self.sidebar, bg=self.SIDEBAR)
        brand.pack(fill="x", padx=20, pady=(22, 24))
        tk.Label(
            brand,
            text="CCNA",
            bg=self.SIDEBAR,
            fg=self.ACCENT,
            font=(self.font_family, 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="EVE LAB BUILDER",
            bg=self.SIDEBAR,
            fg=self.TEXT,
            font=(self.font_family, 10, "bold"),
        ).pack(anchor="w", pady=(0, 3))
        tk.Label(
            brand,
            text=f"{len(self.catalog.all())} training labs",
            bg=self.SIDEBAR,
            fg=self.MUTED,
            font=(self.font_family, 9),
        ).pack(anchor="w")

        nav = tk.Frame(self.sidebar, bg=self.SIDEBAR)
        nav.pack(fill="x", padx=10)

        self._nav_section(nav, "OVERVIEW")
        self._nav_button(nav, "dashboard", "▣  Dashboard", "Dashboard")

        self._nav_section(nav, "LAB ENVIRONMENT")
        self._nav_button(nav, "connection", "●  EVE-NG", "EVE-NG Connection")
        self._nav_button(nav, "images", "◇  IOS Images", "IOS Images")
        self._nav_button(nav, "master", "▦  Master Lab", "Master Lab")

        self._nav_section(nav, "TRAINING")
        self._nav_button(nav, "labs", "◎  Training Labs", "Training Labs")
        self._nav_button(nav, "validator", "✓  Validator", "Live Validator")

        self._nav_section(nav, "SYSTEM")
        self._nav_button(nav, "logs", "≡  Logs", "Application Logs")

        footer = tk.Frame(self.sidebar, bg=self.SIDEBAR)
        footer.pack(side="bottom", fill="x", padx=20, pady=18)
        tk.Label(
            footer,
            text="Scenario V2 • Live Validation",
            bg=self.SIDEBAR,
            fg=self.MUTED,
            font=(self.font_family, 8),
        ).pack(anchor="w")

    def _nav_section(self, parent, text):
        tk.Label(
            parent,
            text=text,
            bg=self.SIDEBAR,
            fg="#64748B",
            font=(self.font_family, 8, "bold"),
        ).pack(fill="x", padx=12, pady=(16, 6), anchor="w")

    def _nav_button(self, parent, key, text, title):
        button = tk.Button(
            parent,
            text=text,
            command=lambda k=key: self.show_page(k),
            anchor="w",
            relief="flat",
            bd=0,
            highlightthickness=0,
            bg=self.SIDEBAR,
            fg=self.MUTED,
            activebackground=self.SURFACE_ALT,
            activeforeground=self.TEXT,
            font=(self.font_family, 10),
            padx=14,
            pady=10,
            cursor="hand2",
        )
        button.pack(fill="x", pady=1)
        self._nav_buttons[key] = button
        self._page_titles[key] = title

    def _build_topbar(self):
        bar = ttk.Frame(self.main_area, style="App.TFrame")
        bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 4))
        bar.grid_columnconfigure(0, weight=1)

        title_box = ttk.Frame(bar, style="App.TFrame")
        title_box.grid(row=0, column=0, sticky="w")
        self.page_title = ttk.Label(title_box, text="Dashboard", style="PageTitle.TLabel")
        self.page_title.pack(anchor="w")
        self.page_subtitle = ttk.Label(
            title_box,
            text="CCNA 200-301 lab orchestration and validation",
            style="Muted.TLabel",
        )
        self.page_subtitle.pack(anchor="w", pady=(2, 0))

        status = tk.Frame(bar, bg=self.BG)
        status.grid(row=0, column=1, sticky="e")
        self.ssh_status = self._status_pill(status, "SSH", False)
        self.api_status = self._status_pill(status, "API", False)

    def _status_pill(self, parent, label, active=False):
        frame = tk.Frame(
            parent,
            bg=self.SURFACE,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        frame.pack(side="left", padx=4)
        dot = tk.Label(
            frame,
            text="●",
            bg=self.SURFACE,
            fg=self.SUCCESS if active else "#475569",
            font=(self.font_family, 8),
        )
        dot.pack(side="left", padx=(9, 4), pady=6)
        tk.Label(
            frame,
            text=label,
            bg=self.SURFACE,
            fg=self.TEXT,
            font=(self.font_family, 8, "bold"),
        ).pack(side="left", padx=(0, 9), pady=6)
        return dot

    def _set_connection_status(self, ssh=None, api=None):
        if ssh is not None:
            self.ssh_status.configure(fg=self.SUCCESS if ssh else self.DANGER)
            if hasattr(self, "dash_ssh"):
                self.dash_ssh.configure(
                    text="CONNECTED" if ssh else "DISCONNECTED",
                    foreground=self.SUCCESS if ssh else self.MUTED,
                )
        if api is not None:
            self.api_status.configure(fg=self.SUCCESS if api else self.DANGER)
            if hasattr(self, "dash_api"):
                self.dash_api.configure(
                    text="CONNECTED" if api else "DISCONNECTED",
                    foreground=self.SUCCESS if api else self.MUTED,
                )

    def show_page(self, key):
        pages = {
            "dashboard": self.t_dashboard,
            "connection": self.t_conn,
            "images": self.t_images,
            "master": self.t_master,
            "labs": self.t_labs,
            "validator": self.t_validate,
            "logs": self.t_logs,
        }
        page = pages[key]
        page.tkraise()
        self._current_page = key
        self.page_title.configure(text=self._page_titles.get(key, key.title()))
        for nav_key, button in self._nav_buttons.items():
            selected = nav_key == key
            button.configure(
                bg=self.SURFACE_ALT if selected else self.SIDEBAR,
                fg=self.ACCENT if selected else self.MUTED,
                font=(self.font_family, 10, "bold" if selected else "normal"),
            )

    def _page_header(self, parent, title, subtitle):
        header = ttk.Frame(parent, style="Page.TFrame")
        header.pack(fill="x", pady=(0, 16))
        ttk.Label(header, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text=subtitle,
            style="Muted.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(4, 0))
        return header

    def _card(self, parent, padding=20):
        outer = tk.Frame(
            parent,
            bg=self.SURFACE,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        inner = ttk.Frame(outer, style="Card.TFrame", padding=padding)
        inner.pack(fill="both", expand=True)
        return outer, inner

    def _dashboard_tab(self):
        self._page_header(
            self.t_dashboard,
            "CCNA Lab Builder",
            "A focused workspace for EVE-NG connectivity, lab creation and live IOS validation.",
        )

        cards = ttk.Frame(self.t_dashboard, style="Page.TFrame")
        cards.pack(fill="x")
        for col in range(4):
            cards.grid_columnconfigure(col, weight=1)

        items = [
            ("EVE SSH", "DISCONNECTED", "dash_ssh"),
            ("EVE API", "DISCONNECTED", "dash_api"),
            ("TRAINING LABS", str(len(self.catalog.all())), "dash_labs"),
            ("SCENARIO ENGINE", "V2", "dash_engine"),
        ]
        for col, (label, value, attr) in enumerate(items):
            outer, card = self._card(cards, 18)
            outer.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 6))
            ttk.Label(card, text=label, style="CardMuted.TLabel").pack(anchor="w")
            value_label = ttk.Label(card, text=value, style="CardValue.TLabel")
            value_label.pack(anchor="w", pady=(8, 2))
            setattr(self, attr, value_label)

        lower = ttk.Frame(self.t_dashboard, style="Page.TFrame")
        lower.pack(fill="both", expand=True, pady=(16, 0))
        lower.grid_columnconfigure(0, weight=3)
        lower.grid_columnconfigure(1, weight=2)
        lower.grid_rowconfigure(0, weight=1)

        quick_outer, quick = self._card(lower, 24)
        quick_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(quick, text="Quick actions", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            quick,
            text="Jump directly into the most common lab workflow.",
            style="CardMuted.TLabel",
        ).pack(anchor="w", pady=(4, 18))
        actions = ttk.Frame(quick, style="Card.TFrame")
        actions.pack(fill="x")
        ttk.Button(
            actions,
            text="CONNECT TO EVE-NG",
            style="Accent.TButton",
            command=lambda: self.show_page("connection"),
        ).pack(fill="x", pady=4)
        ttk.Button(
            actions,
            text="BROWSE TRAINING LABS",
            command=lambda: self.show_page("labs"),
        ).pack(fill="x", pady=4)
        ttk.Button(
            actions,
            text="OPEN LIVE VALIDATOR",
            command=lambda: self.show_page("validator"),
        ).pack(fill="x", pady=4)

        info_outer, info = self._card(lower, 24)
        info_outer.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(info, text="Environment", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            info,
            text="Existing EVE-NG server\nIOSv + IOSvL2\nSSH + Web/API\nVerified runtime console\nStructured validation",
            style="CardMuted.TLabel",
            justify="left",
        ).pack(anchor="w", pady=(14, 0))

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

    def field(self, parent, label, row, value="", secret=False):
        ttk.Label(parent, text=label, style="CardMuted.TLabel").grid(
            row=row, column=0, sticky="w", pady=8, padx=(0, 18)
        )
        entry = ttk.Entry(parent, width=50, show="*" if secret else "")
        entry.insert(0, str(value))
        entry.grid(row=row, column=1, sticky="ew", pady=8)
        parent.grid_columnconfigure(1, weight=1)
        return entry

    def _connection_tab(self):
        self._page_header(
            self.t_conn,
            "EVE-NG Connection",
            "Connect to the existing EVE-NG server using separate SSH/CLI and Web/API credentials.",
        )
        outer, f = self._card(self.t_conn, 24)
        outer.pack(fill="x")
        eve = self.settings.data["eve"]
        self.host = self.field(f, "EVE-NG Host", 0, eve["host"])

        ttk.Separator(f).grid(row=1, column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Label(f, text="SSH / CLI", style="Section.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(2, 4)
        )
        self.ssh_user = self.field(f, "SSH Username", 3, eve.get("ssh_username", "root"))
        self.ssh_password = self.field(f, "SSH Password", 4, "", True)
        self.ssh_port = self.field(f, "SSH Port", 5, eve["ssh_port"])

        ttk.Separator(f).grid(row=6, column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Label(f, text="EVE Web / API", style="Section.TLabel").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(2, 4)
        )
        self.api_user = self.field(f, "API Username", 8, eve.get("api_username", "admin"))
        self.api_password = self.field(f, "API Password", 9, "", True)
        self.https = tk.BooleanVar(value=eve["https"])
        ttk.Checkbutton(
            f,
            text="Use HTTPS API (EVE-NG Pro)",
            variable=self.https,
        ).grid(row=10, column=1, sticky="w", pady=(8, 2))
        ttk.Label(
            f,
            text="Community normally uses HTTP. Pro can use HTTPS with native-console API login.",
            style="CardMuted.TLabel",
        ).grid(row=11, column=1, sticky="w", pady=(2, 12))
        ttk.Button(
            f,
            text="TEST SSH + API",
            style="Accent.TButton",
            command=lambda: self.bg(self.test_connection),
        ).grid(row=12, column=1, sticky="e", pady=(10, 0))

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
        self.after(0, lambda: self._set_connection_status(ssh=True))

        self.log("Connecting to EVE-NG Web/API...")
        self.api = EVEApi(
            host,
            self.api_user.get().strip(),
            self.api_password.get(),
            https=self.https.get(),
        )
        self.api.login()
        self.log("EVE-NG API OK.")
        self.after(0, lambda: self._set_connection_status(api=True))

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
            lambda: messagebox.showinfo("EVE-NG", "SSH + API connection successful."),
        )

    def _images_tab(self):
        self._page_header(
            self.t_images,
            "IOS Images",
            "Select, install or scan user-supplied Cisco IOSv and IOSvL2 QEMU images.",
        )
        grid = ttk.Frame(self.t_images, style="Page.TFrame")
        grid.pack(fill="x")
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        router_outer, router = self._card(grid, 22)
        router_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(router, text="IOSv L3", style="Section.TLabel").pack(anchor="w")
        self.router_label = ttk.Label(
            router,
            text="Not selected",
            style="CardMuted.TLabel",
            wraplength=420,
        )
        self.router_label.pack(anchor="w", pady=(8, 18))
        ttk.Button(
            router,
            text="SELECT IOSv",
            command=lambda: self.pick_image(False),
        ).pack(anchor="w")

        switch_outer, switch = self._card(grid, 22)
        switch_outer.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(switch, text="IOSvL2", style="Section.TLabel").pack(anchor="w")
        self.switch_label = ttk.Label(
            switch,
            text="Not selected",
            style="CardMuted.TLabel",
            wraplength=420,
        )
        self.switch_label.pack(anchor="w", pady=(8, 18))
        ttk.Button(
            switch,
            text="SELECT IOSvL2",
            command=lambda: self.pick_image(True),
        ).pack(anchor="w")

        action_outer, actions = self._card(self.t_images, 22)
        action_outer.pack(fill="x", pady=(16, 0))
        ttk.Label(actions, text="Image operations", style="Section.TLabel").pack(anchor="w")
        row = ttk.Frame(actions, style="Card.TFrame")
        row.pack(fill="x", pady=(16, 0))
        ttk.Button(
            row,
            text="INSTALL SELECTED IMAGES",
            style="Accent.TButton",
            command=lambda: self.bg(self.install_images),
        ).pack(side="left")
        ttk.Button(
            row,
            text="SCAN INSTALLED IMAGES",
            command=lambda: self.bg(self.scan_images),
        ).pack(side="left", padx=8)

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
                self.switch_label.configure(text=f"{path}\nEVE folder: {info['folder']}")
            else:
                self.router_image = (path, info)
                self.router_label.configure(text=f"{path}\nEVE folder: {info['folder']}")
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
        self._page_header(
            self.t_master,
            "Master Lab",
            "Create and control the reusable EVE-NG master topology.",
        )
        outer, f = self._card(self.t_master, 24)
        outer.pack(fill="x")
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
        ).grid(row=2, column=1, sticky="w", pady=(12, 18))

        controls = ttk.Frame(f, style="Card.TFrame")
        controls.grid(row=3, column=0, columnspan=2, sticky="e")
        ttk.Button(
            controls,
            text="BUILD MASTER LAB",
            style="Accent.TButton",
            command=lambda: self.bg(self.build_master),
        ).pack(side="left", padx=4)
        ttk.Button(
            controls,
            text="START ALL",
            command=lambda: self.bg(lambda: self.lab_action("start")),
        ).pack(side="left", padx=4)
        ttk.Button(
            controls,
            text="STOP ALL",
            command=lambda: self.bg(lambda: self.lab_action("stop")),
        ).pack(side="left", padx=4)
        ttk.Button(
            controls,
            text="WIPE ALL",
            style="Danger.TButton",
            command=self.confirm_wipe,
        ).pack(side="left", padx=4)

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
        self.settings.data["compatibility"]["experimental_cabling"] = self.experimental.get()
        self.settings.save()
        self.log("Created: " + lab)

    def current_lab_path(self):
        return self.api.lab_path(self.folder.get().strip(), self.master_name.get().strip())

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
        self._page_header(
            self.t_labs,
            "Training Labs",
            "Choose a scenario, review its objectives and create a fresh EVE-NG lab.",
        )
        body = ttk.Frame(self.t_labs, style="Page.TFrame")
        body.pack(fill="both", expand=True)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, minsize=330)
        body.grid_columnconfigure(1, weight=1)

        list_outer = tk.Frame(
            body,
            bg=self.SURFACE,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        list_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(
            list_outer,
            text=f"LAB CATALOG  •  {len(self.catalog.all())}",
            bg=self.SURFACE,
            fg=self.MUTED,
            font=(self.font_family, 8, "bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(14, 8))
        self.lab_list = tk.Listbox(
            list_outer,
            width=34,
            height=25,
            bg=self.SURFACE,
            fg=self.TEXT,
            selectbackground=self.ACCENT_DARK,
            selectforeground="#FFFFFF",
            activebackground=self.SURFACE_ALT,
            activeforeground=self.TEXT,
            highlightthickness=0,
            bd=0,
            relief="flat",
            font=(self.font_family, 10),
            activestyle="none",
        )
        for scenario in self.catalog.all():
            self.lab_list.insert("end", f"{scenario['id']}  {scenario['name']}")
        self.lab_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.lab_list.bind("<<ListboxSelect>>", self.select_scenario)

        detail_outer, right = self._card(body, 24)
        detail_outer.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.scenario_title = ttk.Label(
            right,
            text="Select a lab",
            style="Section.TLabel",
            font=(self.font_family, 17, "bold"),
        )
        self.scenario_title.pack(anchor="w")
        self.scenario_meta = ttk.Label(right, text="", style="CardMuted.TLabel")
        self.scenario_meta.pack(anchor="w", pady=(5, 12))
        self.scenario_text = tk.Text(
            right,
            height=20,
            wrap="word",
            state="disabled",
            bg=self.INPUT,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            selectbackground=self.ACCENT_DARK,
            relief="flat",
            bd=0,
            padx=16,
            pady=14,
            font=(self.font_family, 10),
            spacing1=2,
            spacing3=4,
        )
        self.scenario_text.pack(fill="both", expand=True, pady=(0, 14))
        ttk.Button(
            right,
            text="CREATE FRESH SCENARIO LAB",
            style="Accent.TButton",
            command=lambda: self.bg(self.create_scenario_lab),
        ).pack(anchor="e")

    def select_scenario(self, _event=None):
        sel = self.lab_list.curselection()
        if not sel:
            return
        self.current_scenario = self.catalog.all()[sel[0]]
        scenario = self.current_scenario
        self.scenario_title.configure(text=f"{scenario['id']} — {scenario['name']}")
        self.scenario_meta.configure(
            text=f"{scenario['domain']}  •  {scenario['difficulty']}  •  {scenario['minutes']} min"
        )
        body = scenario["objective"] + "\n\nTASKS\n" + "\n".join(
            f"{index + 1}. {task}" for index, task in enumerate(scenario["tasks"])
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
        self._page_header(
            self.t_validate,
            "Live Validator",
            "Validate the selected scenario against the exact EVE-NG runtime and IOS console.",
        )
        outer, f = self._card(self.t_validate, 22)
        outer.pack(fill="both", expand=True)

        target = ttk.Frame(f, style="Card.TFrame")
        target.pack(fill="x")
        ttk.Label(target, text="VALIDATION TARGET", style="CardMuted.TLabel").pack(anchor="w")
        self.validation_lab = ttk.Entry(target, width=80)
        self.validation_lab.insert(0, "/CCNA-200-301/CCNA-MASTER-LAB.unl")
        self.validation_lab.pack(fill="x", pady=(6, 12))

        buttons = ttk.Frame(target, style="Card.TFrame")
        buttons.pack(fill="x", pady=(0, 14))
        ttk.Button(
            buttons,
            text="VALIDATE LIVE",
            style="Accent.TButton",
            command=lambda: self.bg(self.validate_live),
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="CLEAR",
            command=lambda: self.validation_output.delete("1.0", "end"),
        ).pack(side="left", padx=8)

        self.validation_output = tk.Text(
            f,
            height=24,
            wrap="word",
            bg=self.INPUT,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            selectbackground=self.ACCENT_DARK,
            relief="flat",
            bd=0,
            padx=16,
            pady=14,
            font=(self.mono_family, 10),
        )
        self.validation_output.pack(fill="both", expand=True)
        self.validation_output.tag_configure("pass", foreground=self.SUCCESS)
        self.validation_output.tag_configure("fail", foreground=self.DANGER)
        self.validation_output.tag_configure("score", foreground=self.ACCENT, font=(self.mono_family, 11, "bold"))
        self.validation_output.tag_configure("muted", foreground=self.MUTED)

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
            self.validation_output.tag_add("score", "1.0", "1.end")
            line_count = int(self.validation_output.index("end-1c").split(".")[0])
            for line in range(1, line_count + 1):
                value = self.validation_output.get(f"{line}.0", f"{line}.end")
                if value.startswith("PASS |"):
                    self.validation_output.tag_add("pass", f"{line}.0", f"{line}.end")
                elif value.startswith("FAIL |"):
                    self.validation_output.tag_add("fail", f"{line}.0", f"{line}.end")
                elif value.lstrip().startswith(("Expected:", "Matched:", "Missing:", "Observed output:")):
                    self.validation_output.tag_add("muted", f"{line}.0", f"{line}.end")

        self.after(0, render)

    def _logs_tab(self):
        self._page_header(
            self.t_logs,
            "Application Logs",
            "Connection, EVE-NG operations, runtime discovery and validation diagnostics.",
        )
        outer, f = self._card(self.t_logs, 16)
        outer.pack(fill="both", expand=True)
        toolbar = ttk.Frame(f, style="Card.TFrame")
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Label(toolbar, text="LIVE CONSOLE", style="CardMuted.TLabel").pack(side="left")
        ttk.Button(
            toolbar,
            text="CLEAR LOGS",
            command=lambda: self._clear_logs(),
        ).pack(side="right")
        self.log_box = tk.Text(
            f,
            height=30,
            state="disabled",
            bg="#070B10",
            fg="#CBD5E1",
            insertbackground=self.TEXT,
            selectbackground=self.ACCENT_DARK,
            relief="flat",
            bd=0,
            padx=14,
            pady=12,
            font=(self.mono_family, 9),
        )
        self.log_box.pack(fill="both", expand=True)

    def _clear_logs(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
