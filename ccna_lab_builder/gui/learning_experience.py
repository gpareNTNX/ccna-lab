"""Live learning experience layered on top of the stable EVE-NG lab runtime."""

from __future__ import annotations

import threading
import time
import tkinter as tk
import types
from tkinter import messagebox, ttk

from ccna_lab_builder.core.learning import (
    build_learning_hint,
    link_runtime_state,
    make_event_history_entry,
    make_validation_history_entry,
    normalize_eve_node_state,
    validation_state_by_node,
    validation_summary,
)
from ccna_lab_builder.core.live_validation import LiveValidator
from ccna_lab_builder.gui.console_workspace import TerminalSessionView


VERSION = "5.0.0"
RUNTIME_POLL_MS = 4000
CONSOLE_DEBOUNCE_MS = 4500
DEFAULT_VALIDATION_INTERVAL = 25
MAX_HISTORY = 100


class LearningExperienceController:
    """Coordinate runtime state, continuous validation, hints, and progress history."""

    def __init__(self, window):
        self.window = window
        self.runtime_state = {}
        self._runtime_poll_inflight = False
        self._runtime_error = None
        self._debounce_job = None
        self._periodic_job = None
        self._validation_lock = threading.Lock()
        self._validation_context = threading.local()
        self._capture_local = threading.local()
        self._failed_results = []
        self._failed_index = 0
        self._history_selection = []
        self._last_continuous_record = None

        learning = window.settings.data.setdefault(
            "learning",
            {
                "continuous_validation": False,
                "validation_interval": DEFAULT_VALIDATION_INTERVAL,
                "history": [],
            },
        )
        learning.setdefault("continuous_validation", False)
        learning.setdefault("validation_interval", DEFAULT_VALIDATION_INTERVAL)
        learning.setdefault("history", [])
        if not isinstance(learning["history"], list):
            learning["history"] = []

        self.continuous_var = tk.BooleanVar(
            value=bool(learning.get("continuous_validation", False))
        )
        self.interval = max(
            15,
            min(120, int(learning.get("validation_interval", DEFAULT_VALIDATION_INTERVAL))),
        )

        self._install_runtime_overlay()
        self._install_topology_controls()
        self._install_validator_controls()
        self._install_learning_coach()
        self._install_progress_page()
        self._install_validation_capture()
        self._install_validation_tracking()
        self._install_console_activity_hook()
        self._install_lab_history_hook()

        self.window._learning_runtime_state = self.runtime_state
        self._schedule_runtime_poll(250)
        self._schedule_periodic_validation()
        self._refresh_progress_page()

    def target_lab(self):
        w = self.window
        mode = getattr(w, "_topology_mode", "master")
        scenario = getattr(w, "current_scenario", None)
        if mode == "scenario" and scenario and hasattr(w, "_scenario_lab_path"):
            try:
                return w._scenario_lab_path(scenario)
            except (AttributeError, tk.TclError):
                pass

        try:
            if w.api and hasattr(w, "current_lab_path"):
                return w.current_lab_path()
        except (AttributeError, tk.TclError):
            pass

        try:
            return str(w.validation_lab.get()).strip()
        except (AttributeError, tk.TclError):
            return ""

    def _scenario(self):
        return getattr(self.window, "current_scenario", None)

    def _scenario_node_names(self):
        scenario = self._scenario() or {}
        topology = scenario.get("topology") or {}
        return {
            str(node.get("name"))
            for node in topology.get("nodes", [])
            if node.get("name")
        }

    def _schedule_runtime_poll(self, delay=RUNTIME_POLL_MS):
        try:
            self.window.after(delay, self._runtime_poll_tick)
        except tk.TclError:
            pass

    def _runtime_poll_tick(self):
        if self.window.api and not self._runtime_poll_inflight:
            lab = self.target_lab()
            if lab:
                self._runtime_poll_inflight = True
                threading.Thread(
                    target=self._runtime_poll_worker,
                    args=(lab,),
                    daemon=True,
                ).start()
        self._schedule_runtime_poll()

    def _runtime_poll_worker(self, lab):
        try:
            payload = self.window.api.nodes(lab).get("data", {})
            states = {}
            if isinstance(payload, dict):
                for value in payload.values():
                    if not isinstance(value, dict):
                        continue
                    name = str(value.get("name") or "").strip()
                    if name:
                        states[name] = normalize_eve_node_state(value.get("status"))
            self.runtime_state = states
            self.window._learning_runtime_state = states
            self._runtime_error = None
            self.window.after(0, self._apply_runtime_state)
        except RuntimeError as exc:
            message = str(exc)
            if message != self._runtime_error:
                self._runtime_error = message
                self.window.log(
                    "Runtime state unavailable for the current topology target: " + message
                )
            self.runtime_state = {}
            self.window._learning_runtime_state = {}
            self.window.after(0, self._apply_runtime_state)
        finally:
            self._runtime_poll_inflight = False

    def _apply_runtime_state(self):
        canvas = getattr(self.window, "topology_canvas", None)
        if canvas is not None:
            canvas.runtime_state = dict(self.runtime_state)
            canvas._queue_redraw()
        self._update_selected_node_ui()

    def refresh_runtime(self):
        lab = self.target_lab()
        if not self.window.api or not lab or self._runtime_poll_inflight:
            return
        self._runtime_poll_inflight = True
        threading.Thread(
            target=self._runtime_poll_worker,
            args=(lab,),
            daemon=True,
        ).start()

    def _selected_node(self):
        canvas = getattr(self.window, "topology_canvas", None)
        return getattr(canvas, "selected_node", None) if canvas else None

    def _update_selected_node_ui(self):
        name = self._selected_node()
        state = self.runtime_state.get(name, "unknown") if name else "unknown"
        if not name:
            self.selected_label.configure(text="Selected device: none")
            self.power_status.configure(text="○ NO DEVICE", fg=self.window.MUTED)
            for button in self.power_buttons:
                button.configure(state="disabled")
            return

        self.selected_label.configure(text=f"Selected device: {name}")
        label, color = {
            "running": ("● RUNNING", self.window.SUCCESS),
            "starting": ("● STARTING", self.window.WARNING),
            "stopped": ("○ STOPPED", self.window.MUTED),
            "unknown": ("? UNKNOWN", self.window.WARNING),
        }.get(state, ("? UNKNOWN", self.window.WARNING))
        self.power_status.configure(text=label, fg=color)
        for button in self.power_buttons:
            button.configure(state="normal")

    def power_selected(self, action):
        node_name = self._selected_node()
        if not node_name:
            return
        threading.Thread(
            target=self._power_worker,
            args=(node_name, action),
            daemon=True,
        ).start()

    def _power_worker(self, node_name, action):
        w = self.window
        try:
            if not w.api:
                raise RuntimeError("Connect to EVE-NG first.")
            lab = self.target_lab()
            if not lab:
                raise RuntimeError("No EVE-NG lab target is selected.")

            if action in {"start", "restart"}:
                active = getattr(w, "_active_lab_controller", None)
                if active is not None:
                    active.switch_to(lab, f"{action.title()} {node_name} from Topology")

            payload = w.api.nodes(lab).get("data", {})
            node_id = None
            if isinstance(payload, dict):
                for key, value in payload.items():
                    if isinstance(value, dict) and value.get("name") == node_name:
                        node_id = int(key)
                        break
            if node_id is None:
                raise RuntimeError(f"Node {node_name} was not found in {lab}.")

            w.log(f"Topology power action: {action.upper()} {node_name} in {lab}")
            if action == "start":
                w.api.start_node(lab, node_id)
            elif action == "stop":
                w.api.stop_node(lab, node_id)
            elif action == "restart":
                w.api.stop_node(lab, node_id)
                time.sleep(1.0)
                w.api.start_node(lab, node_id)
            else:
                raise ValueError(f"Unsupported power action: {action}")

            self._record_event(
                "node_power",
                f"{action.upper()} {node_name}",
                lab=lab,
            )
            time.sleep(0.6)
            self.refresh_runtime()
        except Exception as exc:
            message = str(exc)
            w.log("ERROR: topology power action: " + message)
            w.after(
                0,
                lambda msg=message: messagebox.showerror("Topology Power", msg),
            )

    def _install_runtime_overlay(self):
        topology = self.window.topology_canvas
        topology.runtime_state = {}

        current_draw_node = topology._draw_node

        def draw_node(widget, node, x, y):
            current_draw_node(node, x, y)
            name = str(node.get("name") or "")
            state = widget.runtime_state.get(name, "unknown")
            label, color = {
                "running": ("RUN", widget.SUCCESS),
                "starting": ("BOOT", widget.WARNING),
                "stopped": ("OFF", "#64748B"),
                "unknown": ("?", widget.MUTED),
            }.get(state, ("?", widget.MUTED))
            tag = f"node:{name}"
            widget.canvas.create_text(
                x,
                y + 24,
                text=f"● {label}",
                anchor="center",
                fill=color,
                font=(widget.font_family, 7, "bold"),
                tags=(tag,),
            )

        topology._draw_node = types.MethodType(draw_node, topology)

        current_redraw = topology._redraw

        def redraw(widget):
            current_redraw()
            nodes = widget.topology.get("nodes", [])
            links = widget.topology.get("links", [])
            width = max(widget.canvas.winfo_width(), 760)
            height = max(widget.canvas.winfo_height(), 420)
            topology_width = max(480, width - 245 - 24)
            positions = {}
            for node in nodes:
                name = node.get("name")
                if not name:
                    continue
                positions[name] = (
                    widget._percent(node.get("left", "50%"), topology_width, 70),
                    widget._percent(node.get("top", "50%"), height, 58),
                )

            for index, link in enumerate(links):
                a = link.get("a")
                b = link.get("b")
                if a not in positions or b not in positions:
                    continue
                state = link_runtime_state(
                    widget.runtime_state.get(a, "unknown"),
                    widget.runtime_state.get(b, "unknown"),
                )
                color = {
                    "ready": widget.SUCCESS,
                    "starting": widget.WARNING,
                    "stopped": "#475569",
                    "unknown": widget.MUTED,
                }.get(state, widget.MUTED)
                ax, ay = positions[a]
                bx, by = positions[b]
                mx = (ax + bx) / 2
                my = (ay + by) / 2
                tag = f"runtime-link:{index}"
                widget.canvas.create_oval(
                    mx - 5,
                    my - 5,
                    mx + 5,
                    my + 5,
                    fill=color,
                    outline="#0A1018",
                    width=2,
                    tags=(tag,),
                )

        topology._redraw = types.MethodType(redraw, topology)

    def _install_topology_controls(self):
        w = self.window
        bar = tk.Frame(
            w.t_topology,
            bg=w.SURFACE,
            highlightbackground=w.BORDER,
            highlightthickness=1,
        )
        bar.pack(fill="x", pady=(0, 8), before=w.topology_canvas)

        left = tk.Frame(bar, bg=w.SURFACE)
        left.pack(side="left", fill="x", expand=True, padx=12, pady=8)
        self.selected_label = tk.Label(
            left,
            text="Selected device: none",
            bg=w.SURFACE,
            fg=w.TEXT,
            font=(w.font_family, 9, "bold"),
        )
        self.selected_label.pack(side="left")
        self.power_status = tk.Label(
            left,
            text="○ NO DEVICE",
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 8, "bold"),
        )
        self.power_status.pack(side="left", padx=12)
        tk.Label(
            left,
            text="Link dot = both EVE endpoints running; IOS up/up is validated separately.",
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 8),
        ).pack(side="left", padx=8)

        right = tk.Frame(bar, bg=w.SURFACE)
        right.pack(side="right", padx=10, pady=6)
        self.power_buttons = [
            ttk.Button(right, text="POWER ON", command=lambda: self.power_selected("start")),
            ttk.Button(right, text="POWER OFF", command=lambda: self.power_selected("stop")),
            ttk.Button(right, text="RESTART", command=lambda: self.power_selected("restart")),
        ]
        for button in self.power_buttons:
            button.configure(state="disabled")
            button.pack(side="left", padx=3)
        ttk.Button(right, text="REFRESH", command=self.refresh_runtime).pack(
            side="left", padx=3
        )

        w.topology_canvas.canvas.bind(
            "<ButtonRelease-1>",
            lambda _event: w.after(0, self._update_selected_node_ui),
            add="+",
        )

    def _install_validator_controls(self):
        w = self.window
        parent = w.validation_output.master
        bar = tk.Frame(parent, bg=w.SURFACE)
        bar.pack(fill="x", pady=(0, 10), before=w.validation_output)

        self.continuous_status = tk.Label(
            bar,
            text="● CONTINUOUS VALIDATION OFF",
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 8, "bold"),
        )
        self.continuous_status.pack(side="left")

        tk.Checkbutton(
            bar,
            text="Continuous Validation",
            variable=self.continuous_var,
            command=self._toggle_continuous,
            bg=w.SURFACE,
            fg=w.TEXT,
            selectcolor=w.INPUT,
            activebackground=w.SURFACE,
            activeforeground=w.TEXT,
            font=(w.font_family, 9, "bold"),
        ).pack(side="right")

        tk.Label(
            bar,
            text=(
                f"Debounce {CONSOLE_DEBOUNCE_MS // 1000}s after console activity • "
                f"periodic {self.interval}s"
            ),
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 8),
        ).pack(side="right", padx=12)
        self._update_continuous_status()

    def _toggle_continuous(self):
        enabled = bool(self.continuous_var.get())
        learning = self.window.settings.data.setdefault("learning", {})
        learning["continuous_validation"] = enabled
        learning["validation_interval"] = self.interval
        self.window.settings.save()
        self._update_continuous_status()
        if enabled:
            self.schedule_validation("continuous mode enabled", delay_ms=1500)

    def _update_continuous_status(self, validating=False, detail=""):
        if validating:
            text = "● CONTINUOUS VALIDATION RUNNING"
            color = self.window.ACCENT
        elif self.continuous_var.get():
            text = "● CONTINUOUS VALIDATION ON"
            color = self.window.SUCCESS
        else:
            text = "● CONTINUOUS VALIDATION OFF"
            color = self.window.MUTED
        if detail:
            text += f"  •  {detail}"
        if hasattr(self, "continuous_status"):
            self.continuous_status.configure(text=text, fg=color)

    def _schedule_periodic_validation(self):
        if self._periodic_job is not None:
            try:
                self.window.after_cancel(self._periodic_job)
            except tk.TclError:
                pass
        try:
            self._periodic_job = self.window.after(
                self.interval * 1000,
                self._periodic_validation_tick,
            )
        except tk.TclError:
            self._periodic_job = None

    def _periodic_validation_tick(self):
        self._periodic_job = None
        if self.continuous_var.get() and self._continuous_validation_allowed():
            self._kick_continuous_validation("periodic")
        self._schedule_periodic_validation()

    def _continuous_validation_allowed(self):
        if not self.window.api or not self.window.ssh or not self._scenario():
            return False
        wanted = self._scenario_node_names()
        if not wanted:
            return False
        return any(
            name in wanted and state == "running"
            for name, state in self.runtime_state.items()
        )

    def schedule_validation(self, reason, delay_ms=CONSOLE_DEBOUNCE_MS):
        if not self.continuous_var.get():
            return
        if self._debounce_job is not None:
            try:
                self.window.after_cancel(self._debounce_job)
            except tk.TclError:
                pass
        try:
            self._debounce_job = self.window.after(
                delay_ms,
                lambda: self._kick_continuous_validation(reason),
            )
        except tk.TclError:
            self._debounce_job = None

    def _kick_continuous_validation(self, reason):
        self._debounce_job = None
        if not self.continuous_var.get() or not self._continuous_validation_allowed():
            return
        if self._validation_lock.locked():
            self.window.log(
                "Continuous validation skipped because another validation is running."
            )
            return

        threading.Thread(
            target=self._continuous_worker,
            args=(reason,),
            daemon=True,
        ).start()

    def _continuous_worker(self, reason):
        self._validation_context.source = "continuous"
        self.window.after(
            0,
            lambda: self._update_continuous_status(True, reason),
        )
        try:
            self.window.log(f"Continuous validation triggered: {reason}")
            self.window.validate_live()
        except Exception as exc:
            self.window.log("Continuous validation deferred: " + str(exc))
        finally:
            try:
                del self._validation_context.source
            except AttributeError:
                pass
            self.window.after(0, self._update_continuous_status)

    def _install_validation_capture(self):
        current = LiveValidator.validate
        if getattr(current, "_learning_capture", False):
            return

        controller = self

        def validate(validator, lab, scenario):
            results = current(validator, lab, scenario)
            controller._capture_local.results = list(results)
            controller._capture_local.lab = str(lab)
            return results

        validate._learning_capture = True
        LiveValidator.validate = validate

    def _install_validation_tracking(self):
        w = self.window
        current = w.validate_live
        controller = self

        def validate_live(self_window):
            source = getattr(controller._validation_context, "source", "manual")
            blocking = source != "continuous"
            if not controller._validation_lock.acquire(blocking=blocking):
                return None

            controller._capture_local.results = None
            controller._capture_local.lab = ""
            started = time.monotonic()
            try:
                return current()
            finally:
                duration = time.monotonic() - started
                results = getattr(controller._capture_local, "results", None)
                lab = getattr(controller._capture_local, "lab", "") or controller.target_lab()
                if results is not None:
                    controller._accept_validation_results(
                        results,
                        source=source,
                        lab=lab,
                        duration=duration,
                    )
                controller._validation_lock.release()

        validate_live.__name__ = "validate_live"
        w.validate_live = types.MethodType(validate_live, w)

    def _accept_validation_results(self, results, source, lab, duration):
        summary = validation_summary(results)
        validation = validation_state_by_node(results)
        failed = [result for result in results if not result.passed]
        self._failed_results = failed
        self._failed_index = 0

        def apply():
            self.window.topology_canvas.set_validation(validation, summary["score"])
            self._refresh_learning_coach()
            self._update_continuous_status(
                False,
                f"last score {summary['score']}%",
            )

        self.window.after(0, apply)
        self._record_validation(results, source, lab, duration)

    def _install_console_activity_hook(self):
        current = TerminalSessionView._send
        if getattr(current, "_learning_activity", False):
            return

        def send(view, payload):
            result = current(view, payload)
            controller = getattr(view.window, "_learning_controller", None)
            if controller is not None:
                data = payload.encode() if isinstance(payload, str) else payload
                if b"\r" in data or b"\n" in data:
                    controller.schedule_validation(
                        f"console activity on {view.node_name}"
                    )
            return result

        send._learning_activity = True
        TerminalSessionView._send = send

    def _install_learning_coach(self):
        w = self.window
        parent = w.validation_output.master
        outer = tk.Frame(
            parent,
            bg=w.SURFACE_ALT,
            highlightbackground=w.BORDER,
            highlightthickness=1,
        )
        outer.pack(fill="x", pady=(10, 0))

        head = tk.Frame(outer, bg=w.SURFACE_ALT)
        head.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(
            head,
            text="LEARNING COACH",
            bg=w.SURFACE_ALT,
            fg=w.ACCENT,
            font=(w.font_family, 9, "bold"),
        ).pack(side="left")
        self.coach_target = tk.Label(
            head,
            text="Validate a lab to unlock progressive hints.",
            bg=w.SURFACE_ALT,
            fg=w.MUTED,
            font=(w.font_family, 8),
        )
        self.coach_target.pack(side="left", padx=10)

        controls = tk.Frame(head, bg=w.SURFACE_ALT)
        controls.pack(side="right")
        ttk.Button(controls, text="HINT", command=lambda: self.show_hint(1)).pack(
            side="left", padx=2
        )
        ttk.Button(controls, text="EXPLAIN", command=lambda: self.show_hint(2)).pack(
            side="left", padx=2
        )
        ttk.Button(
            controls,
            text="SHOW REMEDIATION",
            command=lambda: self.show_hint(3),
        ).pack(side="left", padx=2)
        ttk.Button(controls, text="NEXT ISSUE", command=self.next_failed_check).pack(
            side="left", padx=2
        )

        self.coach_text = tk.Label(
            outer,
            text="No failed validation check is selected.",
            bg=w.SURFACE_ALT,
            fg=w.TEXT,
            anchor="w",
            justify="left",
            wraplength=980,
            font=(w.font_family, 9),
        )
        self.coach_text.pack(fill="x", padx=12, pady=(4, 10))

    def _current_failed_result(self):
        if not self._failed_results:
            return None
        self._failed_index %= len(self._failed_results)
        return self._failed_results[self._failed_index]

    def _refresh_learning_coach(self):
        result = self._current_failed_result()
        if result is None:
            self.coach_target.configure(text="All current checks passed.")
            self.coach_text.configure(
                text="No remediation needed. Continue to the next objective or lab."
            )
            return
        self.coach_target.configure(
            text=f"Issue {self._failed_index + 1}/{len(self._failed_results)} • "
            f"{result.node} • {result.command}"
        )
        self.coach_text.configure(
            text="Use HINT first. EXPLAIN adds diagnostic context; SHOW REMEDIATION reveals commands."
        )

    def show_hint(self, level):
        result = self._current_failed_result()
        if result is None:
            self.coach_text.configure(text="No failed check is available.")
            return
        hint = build_learning_hint(result)
        if level == 1:
            text = hint.hint
        elif level == 2:
            text = hint.explanation
        else:
            if hint.remediation:
                text = "Suggested remediation:\n" + "\n".join(
                    f"  {command}" for command in hint.remediation
                )
            else:
                text = (
                    "No direct command sequence is defined for this check. "
                    "Use the HINT and EXPLAIN views, then re-run the validation command."
                )
        self.coach_text.configure(text=text)

    def next_failed_check(self):
        if not self._failed_results:
            return
        self._failed_index = (self._failed_index + 1) % len(self._failed_results)
        self._refresh_learning_coach()

    def _history(self):
        learning = self.window.settings.data.setdefault("learning", {})
        history = learning.setdefault("history", [])
        if not isinstance(history, list):
            history = []
            learning["history"] = history
        return history

    def _save_history(self):
        history = self._history()
        del history[:-MAX_HISTORY]
        self.window.settings.save()
        self.window.after(0, self._refresh_progress_page)

    def _record_validation(self, results, source, lab, duration):
        scenario = self._scenario() or {}
        entry = make_validation_history_entry(
            scenario,
            lab,
            results,
            source,
            duration,
        )

        if source == "continuous":
            previous = self._last_continuous_record
            now = time.monotonic()
            if (
                previous
                and previous["scenario_id"] == entry["scenario_id"]
                and previous["score"] == entry["score"]
                and now - previous["monotonic"] < 120
            ):
                return
            self._last_continuous_record = {
                "scenario_id": entry["scenario_id"],
                "score": entry["score"],
                "monotonic": now,
            }

        self._history().append(entry)
        self._save_history()

    def _record_event(self, kind, detail, lab=None):
        entry = make_event_history_entry(
            kind,
            self._scenario(),
            lab or self.target_lab(),
            detail,
        )
        self._history().append(entry)
        self._save_history()

    def _install_lab_history_hook(self):
        w = self.window
        current = w.create_scenario_lab
        controller = self

        def create_scenario_lab(self_window):
            scenario = getattr(self_window, "current_scenario", None)
            lab = (
                self_window._scenario_lab_path(scenario)
                if scenario and hasattr(self_window, "_scenario_lab_path")
                else controller.target_lab()
            )
            result = current()
            controller._record_event(
                "lab_created",
                "Scenario lab created/rebuilt",
                lab=lab,
            )
            self_window.after(800, controller.refresh_runtime)
            return result

        create_scenario_lab.__name__ = "create_scenario_lab"
        w.create_scenario_lab = types.MethodType(create_scenario_lab, w)

    def _install_progress_page(self):
        w = self.window
        w.t_learning = ttk.Frame(w.page_host, style="Page.TFrame")
        w.t_learning.grid(row=0, column=0, sticky="nsew")

        header = tk.Frame(w.t_learning, bg=w.BG)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(
            header,
            text="Learning Progress",
            bg=w.BG,
            fg=w.TEXT,
            font=(w.font_family, 20, "bold"),
        ).pack(side="left")
        self.progress_summary = tk.Label(
            header,
            text="No validation attempts yet.",
            bg=w.BG,
            fg=w.MUTED,
            font=(w.font_family, 9),
        )
        self.progress_summary.pack(side="right")

        stats = tk.Frame(w.t_learning, bg=w.BG)
        stats.pack(fill="x", pady=(0, 10))
        self.progress_cards = {}
        for key, label in (
            ("latest", "LATEST SCORE"),
            ("best", "BEST SCORE"),
            ("attempts", "ATTEMPTS"),
            ("remaining", "CURRENT ISSUES"),
        ):
            card = tk.Frame(
                stats,
                bg=w.SURFACE,
                highlightbackground=w.BORDER,
                highlightthickness=1,
            )
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))
            tk.Label(
                card,
                text=label,
                bg=w.SURFACE,
                fg=w.MUTED,
                font=(w.font_family, 8, "bold"),
            ).pack(anchor="w", padx=12, pady=(10, 2))
            value = tk.Label(
                card,
                text="—",
                bg=w.SURFACE,
                fg=w.ACCENT,
                font=(w.font_family, 20, "bold"),
            )
            value.pack(anchor="w", padx=12, pady=(0, 10))
            self.progress_cards[key] = value

        body = tk.Frame(w.t_learning, bg=w.BG)
        body.pack(fill="both", expand=True)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        left = tk.Frame(
            body,
            bg=w.SURFACE,
            highlightbackground=w.BORDER,
            highlightthickness=1,
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(
            left,
            text="SESSION HISTORY",
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 8, "bold"),
        ).pack(anchor="w", padx=12, pady=(12, 6))
        self.history_list = tk.Listbox(
            left,
            width=44,
            bg=w.SURFACE,
            fg=w.TEXT,
            selectbackground=w.ACCENT_DARK,
            selectforeground="#FFFFFF",
            highlightthickness=0,
            bd=0,
            font=(w.mono_family, 9),
        )
        self.history_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.history_list.bind("<<ListboxSelect>>", self._history_selected)

        right = tk.Frame(
            body,
            bg=w.SURFACE,
            highlightbackground=w.BORDER,
            highlightthickness=1,
        )
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(
            right,
            text="ATTEMPT DETAIL",
            bg=w.SURFACE,
            fg=w.MUTED,
            font=(w.font_family, 8, "bold"),
        ).pack(anchor="w", padx=12, pady=(12, 6))
        self.history_detail = tk.Text(
            right,
            wrap="word",
            state="disabled",
            bg=w.INPUT,
            fg=w.TEXT,
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
            font=(w.mono_family, 9),
        )
        self.history_detail.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        current_show_page = w.show_page

        def show_page(self_window, key):
            if key != "learning":
                return current_show_page(key)
            self_window.t_learning.tkraise()
            self_window._current_page = "learning"
            self_window.page_title.configure(text="Learning Progress")
            self._refresh_progress_page()
            for nav_key, button in self_window._nav_buttons.items():
                selected = nav_key == "learning"
                button.configure(
                    bg=self_window.SURFACE_ALT if selected else self_window.SIDEBAR,
                    fg=self_window.ACCENT if selected else self_window.MUTED,
                )

        w.show_page = types.MethodType(show_page, w)
        nav_parent = w._nav_buttons["validator"].master
        w._nav_button(
            nav_parent,
            "learning",
            "◉  Learning",
            "Learning Progress",
        )
        w._nav_buttons["learning"].configure(
            command=lambda: w.show_page("learning")
        )

    def _refresh_progress_page(self):
        if not hasattr(self, "history_list"):
            return
        history = list(self._history())
        self._history_selection = list(reversed(history))

        self.history_list.delete(0, "end")
        for entry in self._history_selection:
            timestamp = str(entry.get("timestamp", "")).replace("T", " ")[:19]
            scenario_id = entry.get("scenario_id") or "—"
            if entry.get("kind") == "validation":
                label = (
                    f"{timestamp}  {scenario_id:>5}  "
                    f"{entry.get('score', 0):>3}%  {entry.get('source', '')}"
                )
            else:
                label = (
                    f"{timestamp}  {scenario_id:>5}  "
                    f"{entry.get('kind', 'event')}"
                )
            self.history_list.insert("end", label)

        scenario = self._scenario() or {}
        scenario_id = str(scenario.get("id", ""))
        attempts = [
            entry
            for entry in history
            if entry.get("kind") == "validation"
            and (not scenario_id or str(entry.get("scenario_id", "")) == scenario_id)
        ]

        if attempts:
            latest = attempts[-1]
            best = max(int(item.get("score", 0)) for item in attempts)
            current_issues = len(latest.get("failed", []))
            self.progress_cards["latest"].configure(text=f"{latest.get('score', 0)}%")
            self.progress_cards["best"].configure(text=f"{best}%")
            self.progress_cards["attempts"].configure(text=str(len(attempts)))
            self.progress_cards["remaining"].configure(text=str(current_issues))
            name = scenario.get("name") or latest.get("scenario_name") or "Current lab"
            self.progress_summary.configure(
                text=f"{name} • {len(attempts)} validation attempt(s)"
            )
        else:
            for key in self.progress_cards:
                self.progress_cards[key].configure(text="—")
            self.progress_summary.configure(
                text=(
                    f"{scenario.get('name')} • no attempt yet"
                    if scenario.get("name")
                    else "No validation attempts yet."
                )
            )

    def _history_selected(self, _event=None):
        selection = self.history_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self._history_selection):
            return
        entry = self._history_selection[index]
        lines = [
            f"Type: {entry.get('kind', 'event')}",
            f"Time: {entry.get('timestamp', '')}",
            f"Scenario: {entry.get('scenario_id', '')} — {entry.get('scenario_name', '')}",
            f"Lab: {entry.get('lab', '')}",
        ]
        if entry.get("kind") == "validation":
            lines.extend(
                [
                    f"Source: {entry.get('source', '')}",
                    f"Score: {entry.get('score', 0)}%",
                    f"Passed: {entry.get('passed', 0)}/{entry.get('total', 0)}",
                    f"Duration: {entry.get('duration_seconds', 0)}s",
                    "",
                    "Remaining issues:",
                ]
            )
            failed = entry.get("failed", [])
            lines.extend(f"  • {item}" for item in failed)
            if not failed:
                lines.append("  none")
        else:
            lines.append(f"Detail: {entry.get('detail', '')}")

        self.history_detail.configure(state="normal")
        self.history_detail.delete("1.0", "end")
        self.history_detail.insert("1.0", "\n".join(lines))
        self.history_detail.configure(state="disabled")


def install_learning_experience(window):
    """Install the v5 learning layer without changing lab definitions or cabling."""
    if getattr(window, "_learning_experience_installed", False):
        return getattr(window, "_learning_controller", None)

    controller = LearningExperienceController(window)
    window._learning_controller = controller
    window._learning_experience_installed = True

    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except tk.TclError:
        pass

    window.log(
        "Learning Experience v5 enabled: node power controls, runtime link indicators, "
        "continuous validation, progressive hints, and progress history."
    )
    return controller
