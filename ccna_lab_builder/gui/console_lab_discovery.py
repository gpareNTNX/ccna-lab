"""Recursive EVE-NG lab discovery and manual console target selection."""

from __future__ import annotations

import threading
import types
from pathlib import PurePosixPath
import tkinter as tk
from tkinter import messagebox, ttk

from ccna_lab_builder.gui.console_target_compat import (
    _candidate_labs,
    _configured_folder,
    _lab_exists_with_node,
    _normalize_lab,
)


AUTO_LABEL = "AUTO — resolve from active topology"


def _discover_via_ssh(workspace):
    """Return every real .unl path visible under /opt/unetlab/labs."""
    ssh = workspace.window.ssh
    if not ssh:
        return []
    out, _err = ssh.exec(
        "find /opt/unetlab/labs -type f -name '*.unl' -print 2>/dev/null | sort"
    )
    prefix = "/opt/unetlab/labs"
    found = []
    for line in out.splitlines():
        path = line.strip()
        if not path or not path.endswith(".unl"):
            continue
        if path.startswith(prefix):
            path = path[len(prefix):]
        path = _normalize_lab(path)
        if path and path not in found:
            found.append(path)
    return found


def _mode_priority(workspace, path):
    """Lower values are preferred when AUTO mode has multiple real labs."""
    window = workspace.window
    name = PurePosixPath(path).name.upper()
    folder = _configured_folder(window).upper().rstrip("/")
    in_configured_folder = path.upper().startswith(folder + "/") if folder != "/" else True
    mode = getattr(window, "_topology_mode", "master")

    if mode == "scenario":
        scenario = getattr(window, "current_scenario", None) or {}
        scenario_id = str(scenario.get("id", "")).strip()
        prefix = f"CCNA-{scenario_id}-".upper() if scenario_id else ""
        if prefix and name.startswith(prefix):
            return (0 if in_configured_folder else 1, path.upper())
        return (4 if in_configured_folder else 5, path.upper())

    try:
        master_name = window.master_name.get().strip().upper()
    except Exception:
        master_name = ""
    if master_name and name == master_name + ".UNL":
        return (0 if in_configured_folder else 1, path.upper())
    if "MASTER" in name:
        return (2 if in_configured_folder else 3, path.upper())
    return (6 if in_configured_folder else 7, path.upper())


def _selected_override(workspace):
    variable = getattr(workspace, "_eve_lab_override", None)
    if variable is None:
        return ""
    value = str(variable.get() or "").strip()
    if not value or value == AUTO_LABEL:
        return ""
    return _normalize_lab(value)


def _candidate_with_global_scan(workspace, node_name=None):
    """Resolve candidates, then recursively inspect real labs on the EVE host."""
    window = workspace.window
    if not window.api or not window.ssh:
        raise RuntimeError("Connect to EVE-NG SSH + API first.")

    override = _selected_override(workspace)
    if override:
        if _lab_exists_with_node(window.api, override, node_name):
            return override
        raise RuntimeError(
            f"Selected EVE lab {override} does not exist or does not contain node {node_name}. "
            "Choose another lab in Device Console or select AUTO."
        )

    attempted = []
    for candidate in _candidate_labs(workspace):
        if candidate not in attempted:
            attempted.append(candidate)
        if _lab_exists_with_node(window.api, candidate, node_name):
            return candidate

    discovered = _discover_via_ssh(workspace)
    matching = []
    for candidate in sorted(discovered, key=lambda path: _mode_priority(workspace, path)):
        if candidate in attempted:
            continue
        attempted.append(candidate)
        if _lab_exists_with_node(window.api, candidate, node_name):
            matching.append(candidate)

    if not matching:
        sample = ", ".join(discovered[:12]) if discovered else "none"
        mode = getattr(window, "_topology_mode", "master")
        if mode == "scenario":
            scenario = getattr(window, "current_scenario", None) or {}
            label = (
                f"Lab {scenario.get('id')} — {scenario.get('name')}"
                if scenario
                else "the selected scenario"
            )
            raise RuntimeError(
                f"No real EVE-NG lab for {label} contains node {node_name}. "
                f"EVE labs discovered: {sample}. Create the scenario first or use the EVE LAB "
                "selector in Device Console to choose the correct existing lab."
            )
        raise RuntimeError(
            f"No real EVE-NG lab contains Master Topology node {node_name}. "
            f"EVE labs discovered: {sample}. Build the Master Lab first, or use the EVE LAB "
            "selector in Device Console if your existing lab uses a different name/folder."
        )

    # A strongly named scenario/master candidate is safe to select automatically.
    best_priority = _mode_priority(workspace, matching[0])[0]
    best = [path for path in matching if _mode_priority(workspace, path)[0] == best_priority]
    if best_priority <= 3 and len(best) == 1:
        window.log(f"Console AUTO discovery selected EVE lab: {best[0]}")
        return best[0]

    if len(matching) == 1:
        window.log(f"Console AUTO discovery found one EVE lab containing {node_name}: {matching[0]}")
        return matching[0]

    choices = ", ".join(matching[:12])
    raise RuntimeError(
        f"Multiple EVE-NG labs contain node {node_name}: {choices}. "
        "Open Device Console, choose the intended lab from EVE LAB, then double-click the device again."
    )


def _refresh_lab_selector(workspace):
    window = workspace.window
    if not window.ssh:
        messagebox.showerror("Device Console", "Connect to EVE-NG SSH + API first.")
        return
    button = getattr(workspace, "_eve_lab_refresh_button", None)
    if button is not None:
        try:
            button.configure(state="disabled", text="SCANNING…")
        except tk.TclError:
            pass

    def worker():
        try:
            labs = _discover_via_ssh(workspace)
            values = [AUTO_LABEL] + labs
            window.log(f"Device Console discovered {len(labs)} EVE lab(s) under /opt/unetlab/labs.")

            def apply():
                combo = workspace._eve_lab_combo
                current = workspace._eve_lab_override.get()
                combo.configure(values=values)
                if current not in values:
                    workspace._eve_lab_override.set(AUTO_LABEL)
                workspace._eve_lab_count.configure(text=f"{len(labs)} LABS FOUND")
                if button is not None:
                    button.configure(state="normal", text="REFRESH")

            window.after(0, apply)
        except Exception as exc:
            message = str(exc)
            window.log("ERROR: EVE lab discovery: " + message)

            def failed():
                if button is not None:
                    button.configure(state="normal", text="REFRESH")
                messagebox.showerror("Device Console", message)

            window.after(0, failed)

    threading.Thread(target=worker, daemon=True).start()


def _install_selector(workspace):
    if getattr(workspace, "_eve_lab_selector_installed", False):
        return
    window = workspace.window
    row = tk.Frame(window.t_console, bg=window.SURFACE)
    row.pack(fill="x", pady=(0, 8), before=workspace.notebook)

    tk.Label(
        row,
        text="EVE LAB",
        bg=window.SURFACE,
        fg=window.MUTED,
        font=(window.font_family, 8, "bold"),
    ).pack(side="left", padx=(12, 8), pady=9)

    workspace._eve_lab_override = tk.StringVar(value=AUTO_LABEL)
    combo = ttk.Combobox(
        row,
        textvariable=workspace._eve_lab_override,
        values=[AUTO_LABEL],
        state="readonly",
        width=62,
    )
    combo.pack(side="left", fill="x", expand=True, pady=7)
    workspace._eve_lab_combo = combo

    workspace._eve_lab_count = tk.Label(
        row,
        text="NOT SCANNED",
        bg=window.SURFACE,
        fg=window.MUTED,
        font=(window.font_family, 8, "bold"),
    )
    workspace._eve_lab_count.pack(side="left", padx=10)

    refresh = ttk.Button(row, text="REFRESH", command=lambda: _refresh_lab_selector(workspace))
    refresh.pack(side="right", padx=(0, 12), pady=6)
    workspace._eve_lab_refresh_button = refresh

    def changed(_event=None):
        value = workspace._eve_lab_override.get()
        if value == AUTO_LABEL:
            workspace.target_label.configure(
                text="AUTO target • double-click a topology device to resolve its real EVE-NG lab."
            )
        else:
            workspace.target_label.configure(
                text=f"Manual EVE target: {value} • double-click a device to open its console."
            )

    combo.bind("<<ComboboxSelected>>", changed)
    workspace._eve_lab_selector_installed = True


def install_global_console_lab_discovery(window):
    """Add recursive real-lab discovery on top of the 4.3.1 target resolver."""
    workspace = getattr(window, "_console_workspace", None)
    if workspace is None or getattr(workspace, "_global_lab_discovery_installed", False):
        return workspace

    _install_selector(workspace)

    workspace.resolve_existing_lab = types.MethodType(
        lambda self, node_name=None: _candidate_with_global_scan(self, node_name),
        workspace,
    )

    # The 4.3.1 TerminalSessionView wrapper calls the module-level resolver from
    # console_target_compat. Replace that symbol so existing connection logic uses
    # this recursive resolver without touching LiveValidator or SSHConnection.
    from ccna_lab_builder.gui import console_target_compat as compat

    compat.resolve_existing_lab = _candidate_with_global_scan

    workspace._global_lab_discovery_installed = True
    try:
        window.winfo_toplevel().title("CCNA 200-301 EVE-NG Lab Builder v4.3.2")
    except tk.TclError:
        pass
    return workspace
