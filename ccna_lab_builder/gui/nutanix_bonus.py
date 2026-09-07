"""Nutanix bonus-lab UI and isolated NX-OSv9K support."""

from __future__ import annotations

import copy
import re
import threading
import types
import tkinter as tk
from tkinter import ttk

from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.core.live_validation import LiveValidator
from ccna_lab_builder.core.nutanix_bonus import NutanixBonusCatalog
from ccna_lab_builder.core.ssh import CiscoConsole
from ccna_lab_builder.gui.console_workspace import ConsoleWorkspace
from ccna_lab_builder.gui.lab_rebuild_console_fix import _prepare_rebuild


VERSION = "5.1.0"
NXOS_USERNAME = "admin"
NXOS_PASSWORD = "NutanixLab!"
NXOS_TEMPLATE = "nxosv9k"


def nxosv9k_image_folders(images):
    """Return EVE QEMU image folders usable by the nxosv9k template."""
    return sorted(
        str(item).strip()
        for item in images
        if str(item).strip().lower().startswith("nxosv9k-")
    )


def _nxos_payload(spec):
    image = str(spec.get("image") or "").strip()
    if not image:
        raise RuntimeError(
            "Nexus 9000v image is not selected. Scan EVE-NG for an nxosv9k-* image first."
        )
    return {
        "type": "qemu",
        "template": NXOS_TEMPLATE,
        "config": spec.get("config", "Unconfigured"),
        "delay": int(spec.get("delay", 0)),
        "icon": spec.get("icon", "Switch.png"),
        "image": image,
        "name": spec["name"],
        "left": str(spec.get("left", "50%")),
        "top": str(spec.get("top", "50%")),
        "ram": str(spec.get("ram", "8192")),
        "console": spec.get("console", "telnet"),
        "cpu": int(spec.get("cpu", 2)),
        "ethernet": int(spec.get("interfaces", 8)),
    }


def _install_nxos_builder_support():
    current = LabBuilder._scenario_node_payload
    if getattr(current, "_nxosv9k_support", False):
        return

    def payload(spec, router_image, switch_image):
        if str(spec.get("template", "")).lower() == NXOS_TEMPLATE:
            return _nxos_payload(spec)
        return current(spec, router_image, switch_image)

    payload._nxosv9k_support = True
    LabBuilder._scenario_node_payload = staticmethod(payload)


def _install_nxos_icon_support():
    current = ConsoleWorkspace._kind_for_node
    if getattr(current, "_nxosv9k_support", False):
        return

    def kind(node):
        if str(node.get("template", "")).lower() == NXOS_TEMPLATE:
            return "switch"
        return current(node)

    kind._nxosv9k_support = True
    ConsoleWorkspace._kind_for_node = staticmethod(kind)


def _first_boot_text(text):
    lower = str(text or "").casefold()
    markers = (
        "abort auto provisioning",
        "enforce secure password standard",
        "basic configuration dialog",
        "enter the password for \"admin\"",
    )
    return any(marker in lower for marker in markers)


def _ensure_nxos_exec(console, username=NXOS_USERNAME, password=NXOS_PASSWORD):
    """Reach an NX-OS privileged prompt, logging in when the image is initialized."""
    transcript = []
    for _ in range(6):
        console.send("")
        output = console.read(1.2)
        transcript.append(output)
        prompt = console._last_prompt(output)
        if prompt and prompt.endswith("#"):
            return prompt

        recent = "\n".join(transcript[-3:])
        if _first_boot_text(recent):
            raise RuntimeError(
                "NX-OS first-boot initialization is not complete. Open Device Console for this "
                "Nexus, answer the POAP/setup prompts, and use admin / NutanixLab! for this "
                "training lab. Then run VALIDATE LIVE again."
            )

        lower = output.casefold()
        if "login:" in lower or "username:" in lower:
            console.send(username)
            challenge = console.read(1.2)
            transcript.append(challenge)
            if "password:" in challenge.casefold():
                console.send(password)
                response = console.read_until_prompt(timeout=5.0)
                transcript.append(response)
                prompt = console._last_prompt(response)
                if prompt and prompt.endswith("#"):
                    return prompt
                if "login incorrect" in response.casefold() or "authentication failed" in response.casefold():
                    break
        elif "password:" in lower:
            console.send(password)
            response = console.read_until_prompt(timeout=5.0)
            transcript.append(response)
            prompt = console._last_prompt(response)
            if prompt and prompt.endswith("#"):
                return prompt

    prompt = console.current_prompt(timeout=3.0)
    if prompt and prompt.endswith("#"):
        return prompt
    tail = "\n".join(transcript[-3:]).strip()
    if len(tail) > 900:
        tail = tail[-900:]
    raise RuntimeError(
        "Validator could not log in to NX-OS. This Bonus lab expects the training credentials "
        f"{username} / {password}. Current console output: {tail or '<none>'}"
    )


def _run_nxos_check(validator, lab, check, node_id, node_info):
    backend = validator._console_backend(lab, node_id, node_info=node_info)
    backend_label = (
        f"{backend['host']}:{backend['port']}"
        if backend["kind"] == "tcp"
        else backend["path"]
    )
    validator.log(
        f"{check['node']}: NX-OS console {backend_label} "
        f"({backend.get('source', 'unknown')})"
    )

    channel = validator.ssh.open_console_backend(backend)
    try:
        console = CiscoConsole(channel)
        prompt = _ensure_nxos_exec(console)
        console.command("terminal length 0", timeout=5.0)
        output = console.command(check["command"], timeout=10.0)
        result = validator.validator.validate_output(check, output)
        context = (
            f"[Validator target] lab={lab}; lab_uuid={validator._active_lab_uuid}; "
            f"node_id={node_id}; uuid={node_info.get('uuid', 'unknown')}; "
            f"prompt={prompt}; backend={backend_label} "
            f"({backend.get('source', 'unknown')}); "
            f"pid={backend.get('pid', 'n/a')}; "
            f"runtime={backend.get('runtime_dir', 'n/a')}"
        )
        result.output = context + ("\n" + result.output if result.output else "")
        if result.passed:
            validator.log(f"{check['node']}: NX-OS validation PASS")
        else:
            validator.log(
                f"{check['node']}: NX-OS validation FAIL; missing: "
                + ", ".join(result.missing)
            )
        return result
    finally:
        channel.close()


def _install_nxos_validator_support():
    current = LiveValidator.run_check
    if getattr(current, "_nxosv9k_support", False):
        return

    def run_check(self, lab, check):
        nodes = self._node_map(lab)
        if check["node"] not in nodes:
            raise RuntimeError(f"Node {check['node']} not found in {lab}.")
        node_id, node_info = nodes[check["node"]]
        if str(node_info.get("template", "")).lower() != NXOS_TEMPLATE:
            return current(self, lab, check)
        return _run_nxos_check(self, lab, check, node_id, node_info)

    run_check._nxosv9k_support = True
    LiveValidator.run_check = run_check


def _bonus_folder(window):
    base = window.folder.get().strip() or "/CCNA-200-301"
    if not base.startswith("/"):
        base = "/" + base
    return base.rstrip("/") + "/NUTANIX-BONUS"


def _bonus_lab_name(scenario):
    slug = re.sub(r"[^A-Z0-9]+", "-", scenario["name"].upper()).strip("-")
    return f"{scenario['id']}-{slug}"


def _bonus_lab_path(window, scenario):
    return f"{_bonus_folder(window)}/{_bonus_lab_name(scenario)}.unl"


def _scenario_with_image(scenario, image):
    materialized = copy.deepcopy(scenario)
    for node in materialized.get("topology", {}).get("nodes", []):
        if str(node.get("template", "")).lower() == NXOS_TEMPLATE:
            node["image"] = image
    return materialized


def _render_topology(window, scenario):
    window.topology_canvas.set_topology(
        scenario["topology"],
        title=f"{scenario['id']} — {scenario['name']}",
        subtitle="Bonus Nutanix • Cisco Nexus 9000v • KB-2455",
    )
    window._topology_mode = "scenario"


class NutanixBonusController:
    def __init__(self, window):
        self.window = window
        self.catalog = NutanixBonusCatalog()
        self.current = None
        self.image_var = tk.StringVar(value="")
        self.image_status = None
        self.create_button = None
        self._install_scenario_path_route()
        self._install_page()

    def _install_scenario_path_route(self):
        w = self.window
        current = w._scenario_lab_path
        if getattr(current, "_nutanix_bonus_route", False):
            return

        def scenario_lab_path(self_window, scenario):
            if isinstance(scenario, dict) and scenario.get("catalog") == "nutanix_bonus":
                return _bonus_lab_path(self_window, scenario)
            return current(scenario)

        scenario_lab_path._nutanix_bonus_route = True
        w._scenario_lab_path = types.MethodType(scenario_lab_path, w)

    def scan_images(self):
        w = self.window
        if not w.ssh:
            self.image_var.set("")
            self.image_status.configure(
                text="Connect SSH + API, then scan for Nexus 9000v images.",
                fg=w.WARNING,
            )
            self.create_button.configure(state="disabled")
            return []

        images = nxosv9k_image_folders(w.ssh.installed_qemu_images())
        self.image_combo.configure(values=images)
        if images:
            if self.image_var.get() not in images:
                self.image_var.set(images[-1])
            self.image_status.configure(
                text=f"✓ {len(images)} NX-OSv9K image(s) detected on EVE-NG",
                fg=w.SUCCESS,
            )
            self.create_button.configure(state="normal" if self.current else "disabled")
        else:
            self.image_var.set("")
            self.image_status.configure(
                text="No nxosv9k-* image found under /opt/unetlab/addons/qemu.",
                fg=w.DANGER,
            )
            self.create_button.configure(state="disabled")
        return images

    def select(self, index):
        labs = self.catalog.all()
        if index < 0 or index >= len(labs):
            return
        self.current = labs[index]
        w = self.window
        w.current_nutanix_bonus = self.current
        w.current_scenario = self.current
        self.title.configure(text=f"{self.current['id']} — {self.current['name']}")
        self.meta.configure(
            text=(
                f"{self.current['domain']} • {self.current['difficulty']} • "
                f"{self.current['minutes']} min"
            )
        )
        lines = [self.current["objective"], "", "TASKS"]
        lines.extend(
            f"{number}. {task}"
            for number, task in enumerate(self.current["tasks"], start=1)
        )
        lines.extend(["", "LAB NOTES"])
        lines.extend(f"• {note}" for note in self.current.get("notes", []))
        lines.extend(["", "SOURCE BASIS"])
        lines.extend(f"• {item}" for item in self.current.get("source_basis", []))
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", "\n".join(lines))
        self.detail.configure(state="disabled")
        w._set_validation_target(_bonus_lab_path(w, self.current))
        _render_topology(w, self.current)
        if self.image_var.get():
            self.create_button.configure(state="normal")
        self.topology_button.configure(state="normal")
        self.validator_button.configure(state="normal")

    def create_lab(self):
        w = self.window
        if not self.current:
            raise RuntimeError("Select a Nutanix Bonus lab first.")
        if not w.api or not w.ssh:
            raise RuntimeError("Connect to EVE-NG SSH + API first.")
        image = self.image_var.get().strip()
        if not image:
            raise RuntimeError("Scan and select an installed nxosv9k-* image first.")

        scenario = _scenario_with_image(self.current, image)
        target = _bonus_lab_path(w, scenario)
        active = getattr(w, "_active_lab_controller", None)
        if active is not None:
            active.switch_to(target, f"Building Nutanix Bonus {scenario['id']}")
        _prepare_rebuild(w, target)

        w.log(f"Nutanix Bonus: using EVE NX-OSv9K image {image}")
        lab = LabBuilder(w.api, w.log).create_scenario(
            _bonus_folder(w),
            _bonus_lab_name(scenario),
            "",
            "",
            scenario,
            cable=True,
        )
        if active is not None:
            active.mark_active(lab)
        w.current_scenario = self.current
        w._set_validation_target(lab)
        w.log("Nutanix Bonus lab created: " + lab)
        w.log(
            "NX-OS first boot: if prompted, open N9K-01/N9K-02 consoles and initialize "
            f"with training credentials {NXOS_USERNAME} / {NXOS_PASSWORD}."
        )
        w.after(0, lambda: _render_topology(w, self.current))
        return lab

    def open_topology(self):
        if not self.current:
            return
        self.window.current_scenario = self.current
        _render_topology(self.window, self.current)
        self.window._nav_buttons["topology"].invoke()

    def open_validator(self):
        if not self.current:
            return
        self.window.current_scenario = self.current
        self.window._set_validation_target(_bonus_lab_path(self.window, self.current))
        self.window.show_page("validator")

    def show_page(self):
        w = self.window
        w.t_nutanix_bonus.tkraise()
        w._current_page = "nutanix_bonus"
        w.page_title.configure(text="Bonus Nutanix")
        for nav_key, button in w._nav_buttons.items():
            button.configure(
                bg=w.SURFACE_ALT if nav_key == "nutanix_bonus" else w.SIDEBAR,
                fg=w.ACCENT if nav_key == "nutanix_bonus" else w.MUTED,
            )
        if w.ssh:
            threading.Thread(target=self.scan_images, daemon=True).start()

    def _install_page(self):
        w = self.window
        w.t_nutanix_bonus = ttk.Frame(w.page_host, style="Page.TFrame")
        w.t_nutanix_bonus.grid(row=0, column=0, sticky="nsew")

        head = ttk.Frame(w.t_nutanix_bonus, style="Page.TFrame")
        head.pack(fill="x", pady=(0, 12))
        ttk.Label(head, text="Bonus Nutanix", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            head,
            text="Nutanix-focused labs on EVE-NG • isolated from CCNA labs 01-37",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        image_bar = tk.Frame(
            w.t_nutanix_bonus,
            bg=w.SURFACE,
            highlightbackground=w.BORDER,
            highlightthickness=1,
        )
        image_bar.pack(fill="x", pady=(0, 12))
        tk.Label(
            image_bar,
            text="NEXUS 9000V IMAGE",
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 8, "bold"),
        ).pack(side="left", padx=(12, 8), pady=10)
        self.image_combo = ttk.Combobox(
            image_bar,
            textvariable=self.image_var,
            state="readonly",
            width=36,
        )
        self.image_combo.pack(side="left", padx=4, pady=8)
        ttk.Button(image_bar, text="SCAN EVE", command=self.scan_images).pack(
            side="left", padx=6
        )
        self.image_status = tk.Label(
            image_bar,
            text="Connect SSH + API, then scan for nxosv9k-* images.",
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 8),
        )
        self.image_status.pack(side="left", padx=8)
        tk.Label(
            image_bar,
            text=f"Training NX-OS login: {NXOS_USERNAME} / {NXOS_PASSWORD}",
            bg=w.SURFACE,
            fg=w.ACCENT,
            font=(w.font_family, 8, "bold"),
        ).pack(side="right", padx=12)

        body = ttk.Frame(w.t_nutanix_bonus, style="Page.TFrame")
        body.pack(fill="both", expand=True)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self.listbox = tk.Listbox(
            body,
            width=38,
            bg=w.SURFACE,
            fg=w.TEXT,
            selectbackground=w.ACCENT_DARK,
            selectforeground="#fff",
            highlightthickness=0,
            bd=0,
            font=(w.font_family, 10),
        )
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        labs = self.catalog.all()
        for lab in labs:
            self.listbox.insert("end", f"{lab['id']}  {lab['name']}")

        card = tk.Frame(
            body,
            bg=w.SURFACE,
            highlightbackground=w.BORDER,
            highlightthickness=1,
        )
        card.grid(row=0, column=1, sticky="nsew")
        self.title = tk.Label(
            card,
            text="Select a Nutanix lab",
            bg=w.SURFACE,
            fg=w.TEXT,
            font=(w.font_family, 16, "bold"),
            anchor="w",
        )
        self.title.pack(fill="x", padx=18, pady=(18, 4))
        self.meta = tk.Label(
            card,
            text="",
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 9),
            anchor="w",
        )
        self.meta.pack(fill="x", padx=18)
        self.detail = tk.Text(
            card,
            wrap="word",
            state="disabled",
            bg=w.INPUT,
            fg=w.TEXT,
            relief="flat",
            bd=0,
            padx=14,
            pady=12,
            font=(w.font_family, 10),
        )
        self.detail.pack(fill="both", expand=True, padx=18, pady=14)

        controls = ttk.Frame(card, style="Card.TFrame")
        controls.pack(fill="x", padx=18, pady=(0, 18))
        self.create_button = ttk.Button(
            controls,
            text="CREATE / REBUILD NUTANIX LAB",
            style="Accent.TButton",
            command=lambda: w.bg(self.create_lab),
            state="disabled",
        )
        self.create_button.pack(side="right")
        self.topology_button = ttk.Button(
            controls,
            text="OPEN TOPOLOGY",
            command=self.open_topology,
            state="disabled",
        )
        self.topology_button.pack(side="right", padx=6)
        self.validator_button = ttk.Button(
            controls,
            text="OPEN VALIDATOR",
            command=self.open_validator,
            state="disabled",
        )
        self.validator_button.pack(side="right", padx=6)

        self.listbox.bind(
            "<<ListboxSelect>>",
            lambda _event: self.select(self.listbox.curselection()[0])
            if self.listbox.curselection()
            else None,
        )

        original_show_page = w.show_page

        def show_page(self_window, key):
            if key != "nutanix_bonus":
                return original_show_page(key)
            return self.show_page()

        w.show_page = types.MethodType(show_page, w)
        nav_parent = w._nav_buttons["challenges"].master
        w._nav_button(
            nav_parent,
            "nutanix_bonus",
            "◆  Bonus Nutanix",
            "Bonus Nutanix",
        )
        w._nav_buttons["nutanix_bonus"].configure(command=self.show_page)


def install_nutanix_bonus(window):
    """Install the isolated Nutanix lab pack without altering CCNA scenario data."""
    if getattr(window, "_nutanix_bonus_installed", False):
        return getattr(window, "_nutanix_bonus_controller", None)

    _install_nxos_builder_support()
    _install_nxos_icon_support()
    _install_nxos_validator_support()
    controller = NutanixBonusController(window)
    window._nutanix_bonus_controller = controller
    window._nutanix_bonus_installed = True

    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except tk.TclError:
        pass
    window.log(
        "Nutanix Bonus v5.1 enabled: KB-2455 Nexus vPC lab, nxosv9k image detection, "
        "NX-OS validation login, and isolated Nutanix catalog."
    )
    return controller
