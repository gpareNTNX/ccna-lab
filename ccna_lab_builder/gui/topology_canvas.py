import re
import tkinter as tk
from tkinter import ttk

from ccna_lab_builder.core.topology import LINKS, NODES


class TopologyCanvas(tk.Frame):
    """Dark, EVE-inspired topology visualizer backed by scenario topology data."""

    BG = "#0B0F14"
    SURFACE = "#111827"
    INPUT = "#0F172A"
    BORDER = "#263244"
    TEXT = "#E5E7EB"
    MUTED = "#94A3B8"
    ACCENT = "#22D3EE"
    PURPLE = "#A855F7"
    INDIGO = "#818CF8"
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"

    def __init__(self, parent, font_family="Helvetica Neue", mono_family="Menlo"):
        super().__init__(parent, bg=self.BG)
        self.font_family = font_family
        self.mono_family = mono_family
        self.topology = {"nodes": [], "links": []}
        self.validation = {}
        self.score = None
        self.selected_node = None
        self.title = "Master Lab Topology"
        self.subtitle = "Live graphical representation of the lab definition."
        self._draw_job = None

        header = tk.Frame(self, bg=self.BG)
        header.pack(fill="x", pady=(0, 10))
        title_box = tk.Frame(header, bg=self.BG)
        title_box.pack(side="left", fill="x", expand=True)
        self.title_label = tk.Label(
            title_box, text=self.title, bg=self.BG, fg=self.TEXT, anchor="w",
            font=(self.font_family, 13, "bold"),
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = tk.Label(
            title_box, text=self.subtitle, bg=self.BG, fg=self.MUTED, anchor="w",
            font=(self.font_family, 9),
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))
        self.stats_label = tk.Label(
            header, text="0 NODES  •  0 LINKS", bg=self.SURFACE, fg=self.ACCENT,
            padx=11, pady=6, font=(self.font_family, 8, "bold"),
        )
        self.stats_label.pack(side="right")

        frame = tk.Frame(
            self, bg=self.SURFACE, highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            frame, bg="#0A1018", highlightthickness=0, bd=0, relief="flat",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._queue_redraw)
        self.canvas.bind("<Button-1>", self._canvas_click)

        footer = tk.Frame(self, bg=self.BG)
        footer.pack(fill="x", pady=(8, 0))
        tk.Label(
            footer, text="EVE-NG topology preview", bg=self.BG, fg=self.MUTED,
            font=(self.font_family, 8),
        ).pack(side="left")
        tk.Label(
            footer, text="Click a device to inspect validation details",
            bg=self.BG, fg=self.MUTED, font=(self.font_family, 8),
        ).pack(side="right")

    def set_topology(self, topology, title=None, subtitle=None):
        self.topology = topology or {"nodes": [], "links": []}
        self.selected_node = None
        self.validation = {}
        self.score = None
        if title:
            self.title = title
        if subtitle:
            self.subtitle = subtitle
        self.title_label.configure(text=self.title)
        self.subtitle_label.configure(text=self.subtitle)
        nodes = self.topology.get("nodes", [])
        links = self.topology.get("links", [])
        self.stats_label.configure(text=f"{len(nodes)} NODES  •  {len(links)} LINKS")
        self._queue_redraw()

    def set_validation(self, validation, score=None):
        self.validation = validation or {}
        self.score = score
        self._queue_redraw()

    def _queue_redraw(self, _event=None):
        if self._draw_job is not None:
            try:
                self.after_cancel(self._draw_job)
            except tk.TclError:
                pass
        self._draw_job = self.after(35, self._redraw)

    @staticmethod
    def _percent(value, extent, margin):
        text = str(value or "50%").strip()
        if text.endswith("%"):
            try:
                ratio = max(0.0, min(1.0, float(text[:-1]) / 100.0))
                return margin + ratio * max(1, extent - 2 * margin)
            except ValueError:
                pass
        try:
            return float(text)
        except ValueError:
            return extent / 2

    def _rounded_rect(self, x1, y1, x2, y2, radius=14, **kwargs):
        radius = max(2, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return self.canvas.create_polygon(
            points, smooth=True, splinesteps=16, **kwargs
        )

    def _node_status(self, name):
        data = self.validation.get(name)
        if not data:
            return "pending"
        return data.get("status", "pending")

    def _redraw(self):
        self._draw_job = None
        canvas = self.canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 760)
        height = max(canvas.winfo_height(), 420)
        panel_width = 245
        topology_width = max(480, width - panel_width - 24)
        margin_x = 70
        margin_y = 58

        for x in range(22, int(topology_width), 32):
            for y in range(22, int(height), 32):
                canvas.create_oval(
                    x - 1, y - 1, x + 1, y + 1, fill="#182131", outline=""
                )

        nodes = self.topology.get("nodes", [])
        links = self.topology.get("links", [])
        node_by_name = {
            node.get("name"): node for node in nodes if node.get("name")
        }
        positions = {}
        for node in nodes:
            name = node.get("name")
            if not name:
                continue
            positions[name] = (
                self._percent(node.get("left", "50%"), topology_width, margin_x),
                self._percent(node.get("top", "50%"), height, margin_y),
            )

        self._draw_groups(nodes, positions, topology_width, height)
        for link in links:
            a = link.get("a")
            b = link.get("b")
            if a not in positions or b not in positions:
                continue
            ax, ay = positions[a]
            bx, by = positions[b]
            a_template = node_by_name.get(a, {}).get("template")
            b_template = node_by_name.get(b, {}).get("template")
            if a_template == b_template == "viosl2":
                color = self.PURPLE
            elif a_template == b_template == "vios":
                color = self.ACCENT
            else:
                color = self.INDIGO
            canvas.create_line(ax, ay, bx, by, fill="#05080D", width=6, smooth=True)
            canvas.create_line(ax, ay, bx, by, fill=color, width=2, smooth=True)
            self._draw_interface_label(
                ax + (bx - ax) * 0.18, ay + (by - ay) * 0.18,
                link.get("a_if", ""),
            )
            self._draw_interface_label(
                ax + (bx - ax) * 0.82, ay + (by - ay) * 0.82,
                link.get("b_if", ""),
            )

        for node in nodes:
            name = node.get("name")
            if name in positions:
                self._draw_node(node, *positions[name])

        self._draw_validation_panel(
            width - panel_width - 12, 12, width - 12, height - 12
        )

    def _draw_groups(self, nodes, positions, topology_width, height):
        groups = (
            ("viosl2", "IOSvL2 • Switch Cluster", "#352E62", self.PURPLE),
            ("vios", "IOSv • Router Group", "#123D4A", self.ACCENT),
        )
        for template, title, fill, accent in groups:
            members = [
                positions[node["name"]]
                for node in nodes
                if node.get("template") == template and node.get("name") in positions
            ]
            if len(members) < 2:
                continue
            xs = [item[0] for item in members]
            ys = [item[1] for item in members]
            x1 = max(18, min(xs) - 74)
            x2 = min(topology_width - 18, max(xs) + 74)
            y1 = max(18, min(ys) - 58)
            y2 = min(height - 18, max(ys) + 60)
            self._rounded_rect(
                x1, y1, x2, y2, 16, fill=fill, outline=accent,
                width=1, stipple="gray50",
            )
            self.canvas.create_text(
                x1 + 12, y1 + 10, text=title, anchor="nw", fill="#CBD5E1",
                font=(self.font_family, 8, "bold"),
            )

    def _draw_interface_label(self, x, y, text):
        if not text:
            return
        item = self.canvas.create_text(
            x, y, text=text, fill="#D7E2EE", font=(self.mono_family, 7),
        )
        box = self.canvas.bbox(item)
        if box:
            pad = 3
            rect = self.canvas.create_rectangle(
                box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad,
                fill="#111827", outline="#334155", width=1,
            )
            self.canvas.tag_lower(rect, item)

    def _draw_node(self, node, x, y):
        name = node.get("name", "NODE")
        template = node.get("template", "vios")
        status = self._node_status(name)
        selected = name == self.selected_node
        node_w = 112 if template == "viosl2" else 104
        node_h = 52
        x1, y1 = x - node_w / 2, y - node_h / 2
        x2, y2 = x + node_w / 2, y + node_h / 2
        status_color = {
            "pass": self.SUCCESS,
            "fail": self.DANGER,
            "mixed": self.WARNING,
            "running": self.ACCENT,
            "pending": "#64748B",
        }.get(status, "#64748B")
        outline = status_color if status != "pending" else (
            self.ACCENT if selected else "#3A475A"
        )
        fill = "#202743" if template == "viosl2" else "#17212D"
        tag = f"node:{name}"

        self._rounded_rect(
            x1, y1, x2, y2, 11, fill="#060A0F", outline="", tags=(tag,)
        )
        self._rounded_rect(
            x1, y1 - 2, x2, y2 - 2, 11, fill=fill, outline=outline,
            width=2 if selected or status in {"fail", "mixed"} else 1,
            tags=(tag,),
        )
        icon_x = x1 + 18
        icon_y = y - 2
        if template == "viosl2":
            self.canvas.create_rectangle(
                icon_x - 8, icon_y - 6, icon_x + 8, icon_y + 6,
                fill="#3D4A70", outline=self.INDIGO, width=1, tags=(tag,),
            )
        else:
            self.canvas.create_oval(
                icon_x - 8, icon_y - 8, icon_x + 8, icon_y + 8,
                fill="#153A46", outline=self.ACCENT, width=1, tags=(tag,),
            )
        self.canvas.create_line(
            icon_x - 4, icon_y, icon_x + 4, icon_y,
            fill="#DCE7F4", width=1, tags=(tag,),
        )
        self.canvas.create_text(
            x1 + 33, y - 7, text=name, anchor="w", fill=self.TEXT,
            font=(self.font_family, 8, "bold"), tags=(tag,),
        )
        self.canvas.create_text(
            x1 + 33, y + 9,
            text="Cisco IOSvL2" if template == "viosl2" else "Cisco IOSv",
            anchor="w", fill=self.MUTED, font=(self.font_family, 7), tags=(tag,),
        )
        self.canvas.create_oval(
            x2 - 11, y1 + 7, x2 - 3, y1 + 15,
            fill=status_color, outline="#0A1018", width=1, tags=(tag,),
        )

    def _draw_validation_panel(self, x1, y1, x2, y2):
        self._rounded_rect(
            x1, y1, x2, y2, 14, fill="#101722", outline="#2C3B50", width=1,
        )
        pad = 16
        x = x1 + pad
        y = y1 + 16
        self.canvas.create_text(
            x, y, text="LIVE VALIDATION REPORT", anchor="nw", fill=self.TEXT,
            font=(self.font_family, 9, "bold"),
        )
        y += 24
        if self.score is None:
            self.canvas.create_text(
                x, y, text="Awaiting validation", anchor="nw", fill=self.MUTED,
                font=(self.font_family, 9),
            )
            y += 28
        else:
            if self.score >= 80:
                score_color = self.SUCCESS
            elif self.score >= 60:
                score_color = self.WARNING
            else:
                score_color = self.DANGER
            self.canvas.create_text(
                x, y, text=f"{self.score}%", anchor="nw", fill=score_color,
                font=(self.font_family, 22, "bold"),
            )
            y += 38

        node_names = [
            node.get("name") for node in self.topology.get("nodes", [])
            if node.get("name")
        ]
        passed = sum(self._node_status(name) == "pass" for name in node_names)
        failed = sum(self._node_status(name) == "fail" for name in node_names)
        mixed = sum(self._node_status(name) == "mixed" for name in node_names)
        pending = max(0, len(node_names) - passed - failed - mixed)
        for label, value, color in (
            ("Devices passed", passed, self.SUCCESS),
            ("Devices failed", failed, self.DANGER),
            ("Partial", mixed, self.WARNING),
            ("Not validated", pending, self.MUTED),
        ):
            self.canvas.create_text(
                x, y, text=label, anchor="nw", fill=self.MUTED,
                font=(self.font_family, 8),
            )
            self.canvas.create_text(
                x2 - pad, y, text=str(value), anchor="ne", fill=color,
                font=(self.font_family, 8, "bold"),
            )
            y += 18

        y += 8
        self.canvas.create_line(x, y, x2 - pad, y, fill="#263244", width=1)
        y += 12
        if self.selected_node and self.selected_node in self.validation:
            detail = self.validation[self.selected_node]
            self.canvas.create_text(
                x, y, text=self.selected_node, anchor="nw", fill=self.ACCENT,
                font=(self.font_family, 9, "bold"),
            )
            y += 20
            for check in detail.get("checks", [])[:7]:
                status = check.get("status", "pending")
                marker = "✓" if status == "pass" else "✕" if status == "fail" else "•"
                color = (
                    self.SUCCESS if status == "pass" else
                    self.DANGER if status == "fail" else self.MUTED
                )
                label = check.get("label", "Validation check")
                self.canvas.create_text(
                    x, y, text=f"{marker} {label[:28]}", anchor="nw", fill=color,
                    font=(self.font_family, 8),
                )
                y += 18
        else:
            self.canvas.create_text(
                x, y, text="DEVICE STATUS", anchor="nw", fill=self.MUTED,
                font=(self.font_family, 8, "bold"),
            )
            y += 20
            for name in node_names[:9]:
                status = self._node_status(name)
                marker = {
                    "pass": "✓", "fail": "✕", "mixed": "!",
                    "running": "●", "pending": "○",
                }.get(status, "○")
                color = {
                    "pass": self.SUCCESS, "fail": self.DANGER,
                    "mixed": self.WARNING, "running": self.ACCENT,
                    "pending": self.MUTED,
                }.get(status, self.MUTED)
                self.canvas.create_text(
                    x, y, text=f"{marker}  {name[:24]}", anchor="nw", fill=color,
                    font=(self.font_family, 8),
                )
                y += 18

    def _canvas_click(self, event):
        items = self.canvas.find_overlapping(
            event.x - 2, event.y - 2, event.x + 2, event.y + 2
        )
        selected = None
        for item in reversed(items):
            for tag in self.canvas.gettags(item):
                if tag.startswith("node:"):
                    selected = tag.split(":", 1)[1]
                    break
            if selected:
                break
        self.selected_node = selected
        self._queue_redraw()


def _master_topology():
    nodes = []
    for name, spec in NODES.items():
        item = {"name": name}
        item.update(spec)
        nodes.append(item)
    links = [
        {"a": a, "a_if": a_if, "b": b, "b_if": b_if}
        for a, a_if, b, b_if in LINKS
    ]
    return {"nodes": nodes, "links": links}


def _show_topology(window):
    window.t_topology.tkraise()
    window._current_page = "topology"
    window.page_title.configure(text="Topology Canvas")
    for nav_key, button in window._nav_buttons.items():
        selected = nav_key == "topology"
        button.configure(
            bg=window.SURFACE_ALT if selected else window.SIDEBAR,
            fg=window.ACCENT if selected else window.MUTED,
            font=(window.font_family, 10, "bold" if selected else "normal"),
        )


def _render_master(window):
    window.topology_canvas.set_topology(
        _master_topology(),
        title="CCNA Master Lab",
        subtitle="Reusable nine-device topology defined by the Master Lab builder.",
    )
    window._topology_mode = "master"


def _render_current_scenario(window):
    scenario = getattr(window, "current_scenario", None)
    topology = (scenario or {}).get("topology")
    if not scenario or not topology:
        _render_master(window)
        return
    window.topology_canvas.set_topology(
        topology,
        title=f"Lab {scenario['id']} — {scenario['name']}",
        subtitle=(
            f"{scenario.get('domain', 'CCNA')} • "
            f"{scenario.get('difficulty', '')} • "
            f"{scenario.get('minutes', '?')} min"
        ),
    )
    window._topology_mode = "scenario"


def _sync_selected_scenario(window):
    if getattr(window, "current_scenario", None):
        _render_current_scenario(window)


def _parse_validation_output(text):
    score_match = re.search(r"^Score:\s*(\d+)%", text, re.MULTILINE)
    if not score_match:
        return None, {}
    score = int(score_match.group(1))
    validation = {}
    for line in text.splitlines():
        match = re.match(r"^(PASS|FAIL)\s*\|\s*([^|]+?)\s*\|\s*(.+)$", line)
        if not match:
            continue
        state, node, command = match.groups()
        node = node.strip()
        status = "pass" if state == "PASS" else "fail"
        entry = validation.setdefault(node, {"status": status, "checks": []})
        if entry["status"] != status:
            entry["status"] = "mixed"
        entry["checks"].append({"status": status, "label": command.strip()})
    return score, validation


def _poll_validation(window):
    try:
        text = window.validation_output.get("1.0", "end-1c")
    except tk.TclError:
        return
    signature = hash(text)
    if text and signature != getattr(window, "_topology_validation_signature", None):
        score, validation = _parse_validation_output(text)
        if score is not None:
            window._topology_validation_signature = signature
            if getattr(window, "current_scenario", None):
                _render_current_scenario(window)
            window.topology_canvas.set_validation(validation, score)
    try:
        window.after(650, lambda: _poll_validation(window))
    except tk.TclError:
        pass


def install_topology_workspace(window):
    """Attach an EVE-inspired topology workspace without changing lab behavior."""
    window.t_topology = ttk.Frame(window.page_host, style="Page.TFrame")
    window.t_topology.grid(row=0, column=0, sticky="nsew")

    toolbar = ttk.Frame(window.t_topology, style="Page.TFrame")
    toolbar.pack(fill="x", pady=(0, 10))
    ttk.Button(
        toolbar, text="MASTER TOPOLOGY", command=lambda: _render_master(window),
    ).pack(side="left")
    ttk.Button(
        toolbar, text="CURRENT SCENARIO", style="Accent.TButton",
        command=lambda: _render_current_scenario(window),
    ).pack(side="left", padx=8)
    ttk.Label(
        toolbar,
        text="Scenario-driven • live validation overlay • interface labels",
        style="Muted.TLabel",
    ).pack(side="right")

    window.topology_canvas = TopologyCanvas(
        window.t_topology,
        font_family=window.font_family,
        mono_family=window.mono_family,
    )
    window.topology_canvas.pack(fill="both", expand=True)
    _render_master(window)

    nav_parent = window._nav_buttons["logs"].master
    window._nav_button(nav_parent, "topology", "⌁  Topology", "Topology Canvas")
    window._nav_buttons["topology"].configure(command=lambda: _show_topology(window))
    window.lab_list.bind(
        "<<ListboxSelect>>",
        lambda _event: window.after(0, lambda: _sync_selected_scenario(window)),
        add="+",
    )
    window._topology_validation_signature = None
    window.after(650, lambda: _poll_validation(window))
