"""Interactive EVE-NG device console workspace and topology icon integration."""

from __future__ import annotations

import threading
import types
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from ccna_lab_builder.core.live_validation import LiveValidator
from ccna_lab_builder.core.ssh import CiscoConsole


ASSET_DIR = Path(__file__).resolve().parent / "assets" / "icons"


class DeviceIconLibrary:
    """Load the user-provided network icons once and keep Tk references alive."""

    NAMES = ("router", "switch", "cloud", "terminal", "firewall", "server")

    def __init__(self):
        self.images = {}
        for name in self.NAMES:
            path = ASSET_DIR / f"{name}.png"
            if path.exists():
                try:
                    self.images[name] = tk.PhotoImage(file=str(path))
                except tk.TclError:
                    pass

    def get(self, name):
        return self.images.get(name)


class TerminalSessionView(tk.Frame):
    """Interactive terminal bound to one exact EVE-NG node console backend."""

    def __init__(self, parent, window, node_name, lab):
        super().__init__(parent, bg=window.BG)
        self.window = window
        self.node_name = node_name
        self.lab = lab
        self.channel = None
        self.backend = None
        self._stop = threading.Event()
        self._reader = None
        self._connecting = False
        self._build()

    def _build(self):
        w = self.window
        top = tk.Frame(self, bg=w.SURFACE)
        top.pack(fill="x", pady=(0, 8))

        left = tk.Frame(top, bg=w.SURFACE)
        left.pack(side="left", fill="x", expand=True, padx=14, pady=10)
        tk.Label(
            left,
            text=self.node_name,
            bg=w.SURFACE,
            fg=w.TEXT,
            font=(w.font_family, 11, "bold"),
        ).pack(anchor="w")
        self.backend_label = tk.Label(
            left,
            text=self.lab,
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.mono_family, 8),
        )
        self.backend_label.pack(anchor="w", pady=(2, 0))

        controls = tk.Frame(top, bg=w.SURFACE)
        controls.pack(side="right", padx=12, pady=8)
        self.status = tk.Label(
            controls,
            text="● DISCONNECTED",
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 8, "bold"),
        )
        self.status.pack(side="left", padx=(0, 10))
        ttk.Button(controls, text="RECONNECT", command=self.connect).pack(side="left", padx=3)
        ttk.Button(controls, text="CLEAR", command=self.clear).pack(side="left", padx=3)
        ttk.Button(controls, text="DISCONNECT", command=self.disconnect).pack(side="left", padx=3)

        self.terminal = tk.Text(
            self,
            wrap="none",
            bg="#05080D",
            fg="#D7E2EE",
            insertbackground=w.ACCENT,
            selectbackground=w.ACCENT_DARK,
            relief="flat",
            bd=0,
            padx=14,
            pady=12,
            font=(w.mono_family, 10),
            undo=False,
        )
        self.terminal.pack(fill="both", expand=True)
        self.terminal.insert(
            "end",
            f"CCNA EVE Device Console — {self.node_name}\n"
            f"Target: {self.lab}\n"
            "Connecting through the exact EVE-NG runtime console...\n\n",
        )
        self.terminal.see("end")
        self.terminal.focus_set()

        self.terminal.bind("<KeyPress>", self._key_press)
        self.terminal.bind("<Control-c>", self._copy)
        self.terminal.bind("<Command-c>", self._copy)
        self.terminal.bind("<Control-v>", self._paste)
        self.terminal.bind("<Command-v>", self._paste)
        self.terminal.bind("<Button-1>", lambda _event: self.terminal.focus_set())

        hint = tk.Label(
            self,
            text="Interactive EVE console • Enter/Tab/arrows/Ctrl+C supported • Clipboard paste supported",
            bg=w.BG,
            fg=w.MUTED,
            anchor="w",
            font=(w.font_family, 8),
        )
        hint.pack(fill="x", pady=(6, 0))

    def _set_status(self, text, color):
        try:
            self.status.configure(text=text, fg=color)
        except tk.TclError:
            pass

    def _append(self, text):
        if not text:
            return
        rendered = str(text).replace("\r\n", "\n").replace("\r", "\n")
        try:
            self.terminal.insert("end", rendered)
            self.terminal.see("end")
        except tk.TclError:
            pass

    def clear(self):
        self.terminal.delete("1.0", "end")

    def connect(self):
        if self._connecting:
            return
        if self.channel is not None and not getattr(self.channel, "closed", False):
            self.terminal.focus_set()
            return
        if not self.window.api or not self.window.ssh:
            messagebox.showerror(
                "Device Console",
                "Connect to EVE-NG SSH + API before opening a device console.",
            )
            return
        self._connecting = True
        self._stop.clear()
        self._set_status("● CONNECTING", self.window.ACCENT)
        self._append(f"[Connecting to {self.node_name}...]\n")
        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self):
        try:
            resolver = LiveValidator(self.window.api, self.window.ssh, self.window.log)
            lab_data = self.window.api.get_lab(self.lab).get("data", {})
            resolver._active_lab_uuid = str(lab_data.get("id") or "unknown")
            nodes = resolver._node_map(self.lab)
            if self.node_name not in nodes:
                available = ", ".join(sorted(nodes)) or "none"
                raise RuntimeError(
                    f"Node {self.node_name} was not found in {self.lab}. Available nodes: {available}"
                )
            node_id, node_info = nodes[self.node_name]
            backend = resolver._console_backend(self.lab, node_id, node_info=node_info)
            channel = self.window.ssh.open_console_backend(backend)
            self.backend = backend
            self.channel = channel
            self._reader = threading.Thread(target=self._reader_loop, daemon=True)
            self._reader.start()
            label = (
                f"{backend.get('host')}:{backend.get('port')}"
                if backend.get("kind") == "tcp"
                else backend.get("path", "console")
            )
            source = backend.get("source", "unknown")
            self.window.log(
                f"Interactive console opened: {self.node_name} -> {label} ({source})"
            )
            self.after(
                0,
                lambda: self.backend_label.configure(
                    text=f"{self.lab}  •  {label}  •  {source}"
                ),
            )
            self.after(
                0,
                lambda: self._set_status("● CONNECTED", self.window.SUCCESS),
            )
            self.after(
                0,
                lambda: self._append(f"[Connected via {label} ({source})]\n"),
            )
            try:
                channel.send(b"\r")
            except Exception:
                pass
        except Exception as exc:
            message = str(exc)
            self.window.log("ERROR: interactive console: " + message)
            self.after(
                0,
                lambda msg=message: self._append(f"[Connection failed: {msg}]\n"),
            )
            self.after(
                0,
                lambda: self._set_status("● FAILED", self.window.DANGER),
            )
            self.after(
                0,
                lambda msg=message: messagebox.showerror("Device Console", msg),
            )
        finally:
            self._connecting = False

    def _reader_loop(self):
        channel = self.channel
        if channel is None:
            return
        try:
            while not self._stop.is_set() and not getattr(channel, "closed", False):
                try:
                    if channel.recv_ready():
                        data = channel.recv(65535)
                        if not data:
                            break
                        text = CiscoConsole._clean_telnet(data)
                        self.after(0, lambda payload=text: self._append(payload))
                    else:
                        self._stop.wait(0.035)
                except Exception as exc:
                    if not self._stop.is_set():
                        self.after(
                            0,
                            lambda msg=str(exc): self._append(
                                f"\n[Console read error: {msg}]\n"
                            ),
                        )
                    break
        finally:
            if not self._stop.is_set():
                self.after(
                    0,
                    lambda: self._set_status(
                        "● DISCONNECTED", self.window.MUTED
                    ),
                )

    def _send(self, payload):
        channel = self.channel
        if channel is None or getattr(channel, "closed", False):
            self._append("\n[Console is not connected. Use RECONNECT.]\n")
            return
        try:
            data = payload.encode() if isinstance(payload, str) else payload
            channel.send(data)
        except Exception as exc:
            self._append(f"\n[Send failed: {exc}]\n")
            self._set_status("● FAILED", self.window.DANGER)

    def _key_press(self, event):
        keymap = {
            "Return": b"\r",
            "KP_Enter": b"\r",
            "BackSpace": b"\x08",
            "Tab": b"\t",
            "Up": b"\x1b[A",
            "Down": b"\x1b[B",
            "Right": b"\x1b[C",
            "Left": b"\x1b[D",
            "Home": b"\x01",
            "End": b"\x05",
            "Escape": b"\x1b",
            "Delete": b"\x7f",
        }
        if event.keysym in keymap:
            self._send(keymap[event.keysym])
            return "break"
        if event.char:
            self._send(event.char)
            return "break"
        return "break"

    def _copy(self, _event=None):
        try:
            selected = self.terminal.get("sel.first", "sel.last")
        except tk.TclError:
            return "break"
        self.clipboard_clear()
        self.clipboard_append(selected)
        return "break"

    def _paste(self, _event=None):
        try:
            text = self.clipboard_get()
        except tk.TclError:
            return "break"
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        self._send(text.replace("\n", "\r"))
        return "break"

    def disconnect(self):
        self._stop.set()
        channel = self.channel
        self.channel = None
        if channel is not None:
            try:
                channel.close()
            except Exception:
                pass
        self._set_status("● DISCONNECTED", self.window.MUTED)
        self._append("\n[Disconnected]\n")


class ConsoleWorkspace:
    def __init__(self, window):
        self.window = window
        self.icons = DeviceIconLibrary()
        self.sessions = {}
        self._install_page()
        self._install_topology_icons()
        self._install_topology_console_binding()
        self._set_version_title()

    def _set_version_title(self):
        try:
            self.window.winfo_toplevel().title(
                "CCNA 200-301 EVE-NG Lab Builder v4.3.0"
            )
        except tk.TclError:
            pass

    def _install_page(self):
        w = self.window
        w.t_console = ttk.Frame(w.page_host, style="Page.TFrame")
        w.t_console.grid(row=0, column=0, sticky="nsew")

        toolbar = tk.Frame(w.t_console, bg=w.BG)
        toolbar.pack(fill="x", pady=(0, 10))
        left = tk.Frame(toolbar, bg=w.BG)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(
            left,
            text="Device Console",
            bg=w.BG,
            fg=w.TEXT,
            font=(w.font_family, 14, "bold"),
        ).pack(anchor="w")
        self.target_label = tk.Label(
            left,
            text="Double-click a device in Topology to open its EVE-NG console.",
            bg=w.BG,
            fg=w.MUTED,
            font=(w.font_family, 9),
        )
        self.target_label.pack(anchor="w", pady=(2, 0))
        ttk.Button(
            toolbar,
            text="TOPOLOGY",
            command=self._show_topology,
        ).pack(side="right", padx=4)
        ttk.Button(
            toolbar,
            text="DISCONNECT ALL",
            command=self.disconnect_all,
        ).pack(side="right", padx=4)

        style = ttk.Style(w)
        style.configure("Console.TNotebook", background=w.BG, borderwidth=0)
        style.configure(
            "Console.TNotebook.Tab",
            background=w.SURFACE_ALT,
            foreground=w.MUTED,
            padding=(14, 8),
            font=(w.font_family, 9, "bold"),
        )
        style.map(
            "Console.TNotebook.Tab",
            background=[("selected", w.SURFACE)],
            foreground=[("selected", w.ACCENT)],
        )

        self.notebook = ttk.Notebook(w.t_console, style="Console.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        nav_parent = w._nav_buttons["logs"].master
        w._nav_button(nav_parent, "console", "  Console", "Device Console")
        nav = w._nav_buttons["console"]
        terminal_icon = self.icons.get("terminal")
        if terminal_icon is not None:
            nav.configure(image=terminal_icon, compound="left")
        nav.configure(command=self.show_page)

    def _show_topology(self):
        button = self.window._nav_buttons.get("topology")
        if button is not None:
            try:
                button.invoke()
                return
            except tk.TclError:
                pass

    def show_page(self):
        w = self.window
        w.t_console.tkraise()
        w._current_page = "console"
        w.page_title.configure(text="Device Console")
        lab = self._target_lab(allow_unconnected=True)
        self.target_label.configure(
            text=(
                f"Active target: {lab} • interactive console through EVE-NG runtime"
                if lab
                else "Double-click a device in Topology to open its EVE-NG console."
            )
        )
        for nav_key, button in w._nav_buttons.items():
            selected = nav_key == "console"
            button.configure(
                bg=w.SURFACE_ALT if selected else w.SIDEBAR,
                fg=w.ACCENT if selected else w.MUTED,
                font=(w.font_family, 10, "bold" if selected else "normal"),
            )

    def _target_lab(self, allow_unconnected=False):
        w = self.window
        if not allow_unconnected and (not w.api or not w.ssh):
            raise RuntimeError("Connect to EVE-NG SSH + API first.")
        if getattr(w, "_topology_mode", "master") == "scenario":
            scenario = getattr(w, "current_scenario", None)
            if scenario and hasattr(w, "_scenario_lab_path"):
                return w._scenario_lab_path(scenario)
        try:
            if w.api and hasattr(w, "current_lab_path"):
                return w.current_lab_path()
        except Exception:
            pass
        try:
            folder = w.folder.get().strip() or "/"
            if not folder.startswith("/"):
                folder = "/" + folder
            name = w.master_name.get().strip()
            if name:
                return f"{folder.rstrip('/')}/{name}.unl"
        except Exception:
            pass
        return ""

    def open_device(self, node_name):
        try:
            lab = self._target_lab()
        except Exception as exc:
            messagebox.showerror("Device Console", str(exc))
            return
        if not lab:
            messagebox.showerror(
                "Device Console",
                "No active EVE-NG lab target is available.",
            )
            return
        key = (lab, node_name)
        view = self.sessions.get(key)
        if view is None:
            view = TerminalSessionView(
                self.notebook,
                self.window,
                node_name,
                lab,
            )
            self.sessions[key] = view
            self.notebook.add(view, text=f"  {node_name}  ")
        self.show_page()
        self.notebook.select(view)
        view.terminal.focus_set()
        view.connect()

    def disconnect_all(self):
        for view in list(self.sessions.values()):
            view.disconnect()

    def _node_from_event(self, event):
        canvas = self.window.topology_canvas.canvas
        items = canvas.find_overlapping(
            event.x - 3,
            event.y - 3,
            event.x + 3,
            event.y + 3,
        )
        for item in reversed(items):
            for tag in canvas.gettags(item):
                if tag.startswith("node:"):
                    return tag.split(":", 1)[1]
        return None

    def _install_topology_console_binding(self):
        canvas = self.window.topology_canvas.canvas

        def open_from_canvas(event):
            node_name = self._node_from_event(event)
            if node_name:
                self.window.topology_canvas.selected_node = node_name
                self.window.topology_canvas._queue_redraw()
                self.open_device(node_name)
            return "break"

        canvas.bind("<Double-Button-1>", open_from_canvas, add="+")
        self.window.open_device_console = self.open_device

    @staticmethod
    def _kind_for_node(node):
        icon = str(node.get("icon", "")).lower()
        name = str(node.get("name", "")).lower()
        template = str(node.get("template", "")).lower()
        if "firewall" in icon or "firewall" in name or name.startswith("fw"):
            return "firewall"
        if "server" in icon or "server" in name:
            return "server"
        if "cloud" in icon or "cloud" in name:
            return "cloud"
        if template == "viosl2" or "switch" in icon or name.startswith("sw"):
            return "switch"
        return "router"

    def _install_topology_icons(self):
        topology = self.window.topology_canvas
        original = topology._draw_node
        icons = self.icons

        def draw_icon_node(widget, node, x, y):
            kind = self._kind_for_node(node)
            image = icons.get(kind)
            if image is None:
                return original(node, x, y)

            name = node.get("name", "NODE")
            status = widget._node_status(name)
            selected = name == widget.selected_node
            node_w = 136
            node_h = 66
            x1, y1 = x - node_w / 2, y - node_h / 2
            x2, y2 = x + node_w / 2, y + node_h / 2
            status_color = {
                "pass": widget.SUCCESS,
                "fail": widget.DANGER,
                "mixed": widget.WARNING,
                "running": widget.ACCENT,
                "pending": "#64748B",
            }.get(status, "#64748B")
            outline = (
                status_color
                if status != "pending"
                else widget.ACCENT if selected else "#3A475A"
            )
            tag = f"node:{name}"

            widget._rounded_rect(
                x1,
                y1 + 2,
                x2,
                y2 + 2,
                12,
                fill="#060A0F",
                outline="",
                tags=(tag,),
            )
            widget._rounded_rect(
                x1,
                y1,
                x2,
                y2,
                12,
                fill="#15202B",
                outline=outline,
                width=2 if selected or status in {"fail", "mixed"} else 1,
                tags=(tag,),
            )
            widget.canvas.create_image(
                x1 + 32,
                y,
                image=image,
                anchor="center",
                tags=(tag,),
            )
            widget.canvas.create_text(
                x1 + 62,
                y - 10,
                text=name,
                anchor="w",
                fill=widget.TEXT,
                font=(widget.font_family, 8, "bold"),
                tags=(tag,),
            )
            label = {
                "switch": "Cisco IOSvL2",
                "router": "Cisco IOSv",
                "firewall": "Firewall",
                "server": "Server",
                "cloud": "Network Cloud",
            }.get(kind, kind.title())
            widget.canvas.create_text(
                x1 + 62,
                y + 9,
                text=label,
                anchor="w",
                fill=widget.MUTED,
                font=(widget.font_family, 7),
                tags=(tag,),
            )
            widget.canvas.create_oval(
                x2 - 13,
                y1 + 8,
                x2 - 4,
                y1 + 17,
                fill=status_color,
                outline="#0A1018",
                width=1,
                tags=(tag,),
            )
            widget.canvas.create_text(
                x2 - 7,
                y2 - 8,
                text="⌨",
                anchor="center",
                fill=widget.ACCENT if selected else widget.MUTED,
                font=(widget.font_family, 9, "bold"),
                tags=(tag,),
            )

        topology._draw_node = types.MethodType(draw_icon_node, topology)
        topology._queue_redraw()


def install_console_workspace(window):
    """Install interactive device terminals and user-provided topology icons."""
    if getattr(window, "_console_workspace", None) is not None:
        return window._console_workspace
    workspace = ConsoleWorkspace(window)
    window._console_workspace = workspace
    return workspace
