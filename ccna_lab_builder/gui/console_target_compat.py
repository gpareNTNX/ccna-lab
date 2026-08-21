"""Compatibility layer for resolving real EVE-NG lab targets before opening consoles."""

from __future__ import annotations

import types
from pathlib import PurePosixPath
import tkinter as tk
from tkinter import messagebox

from ccna_lab_builder.gui.console_workspace import TerminalSessionView


def _normalize_lab(value):
    text = str(value or "").strip()
    if not text:
        return ""
    if not text.startswith("/"):
        text = "/" + text
    return text


def _configured_folder(window):
    try:
        folder = window.folder.get().strip() or "/"
    except Exception:
        return "/"
    if not folder.startswith("/"):
        folder = "/" + folder
    return folder.rstrip("/") or "/"


def _validation_target(window):
    try:
        return _normalize_lab(window.validation_lab.get())
    except Exception:
        return ""


def _candidate_labs(workspace):
    window = workspace.window
    mode = getattr(window, "_topology_mode", "master")
    candidates = []

    if mode == "scenario":
        scenario = getattr(window, "current_scenario", None)
        if scenario and hasattr(window, "_scenario_lab_path"):
            try:
                candidates.append(_normalize_lab(window._scenario_lab_path(scenario)))
            except Exception:
                pass
        target = _validation_target(window)
        if target:
            candidates.append(target)
    else:
        try:
            if hasattr(window, "current_lab_path"):
                candidates.append(_normalize_lab(window.current_lab_path()))
        except Exception:
            pass
        try:
            folder = _configured_folder(window)
            name = window.master_name.get().strip()
            if name:
                candidates.append(_normalize_lab(f"{folder.rstrip('/')}/{name}.unl"))
        except Exception:
            pass

    result = []
    for candidate in candidates:
        if candidate and candidate not in result:
            result.append(candidate)
    return result


def _extract_lab_paths(payload, folder):
    """Extract .unl paths from the different folder payload shapes used by EVE builds."""
    found = []
    base = folder.rstrip("/") or "/"

    def add(value):
        text = str(value or "").strip()
        if not text.lower().endswith(".unl"):
            return
        if text.startswith("/"):
            path = text
        else:
            path = f"{base.rstrip('/')}/{text}"
        path = _normalize_lab(path)
        if path and path not in found:
            found.append(path)

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, str):
                    if key.lower() in {
                        "file",
                        "filename",
                        "lab",
                        "name",
                        "path",
                        "fullpath",
                        "full_path",
                    }:
                        add(item)
                    elif item.lower().endswith(".unl"):
                        add(item)
                else:
                    walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            add(value)

    walk(payload)
    return found


def _lab_exists_with_node(api, lab, node_name=None):
    try:
        api.get_lab(lab)
        if not node_name:
            return True
        data = api.nodes(lab).get("data", {})
        names = {
            str(value.get("name", "")).strip()
            for value in data.values()
            if isinstance(value, dict)
        }
        return node_name in names
    except RuntimeError:
        return False


def _mode_matching_discovered_labs(workspace, discovered):
    window = workspace.window
    mode = getattr(window, "_topology_mode", "master")

    if mode == "scenario":
        scenario = getattr(window, "current_scenario", None) or {}
        scenario_id = str(scenario.get("id", "")).strip()
        if not scenario_id:
            return discovered
        prefix = f"CCNA-{scenario_id}-".upper()
        matching = [
            path
            for path in discovered
            if PurePosixPath(path).name.upper().startswith(prefix)
        ]
        return matching or discovered

    try:
        master_name = window.master_name.get().strip().upper()
    except Exception:
        master_name = ""
    if not master_name:
        return discovered

    wanted = master_name + ".UNL"
    return [
        path
        for path in discovered
        if PurePosixPath(path).name.upper() == wanted
    ]


def resolve_existing_lab(workspace, node_name=None):
    """Resolve and verify the real lab backing the topology currently shown."""
    window = workspace.window
    if not window.api or not window.ssh:
        raise RuntimeError("Connect to EVE-NG SSH + API first.")

    attempted = []
    for candidate in _candidate_labs(workspace):
        attempted.append(candidate)
        if _lab_exists_with_node(window.api, candidate, node_name):
            return candidate

    folder = _configured_folder(window)
    try:
        folder_payload = window.api.folder(folder)
    except RuntimeError:
        folder_payload = {}

    discovered = _extract_lab_paths(folder_payload, folder)
    discovered = _mode_matching_discovered_labs(workspace, discovered)
    for candidate in discovered:
        if candidate in attempted:
            continue
        attempted.append(candidate)
        if _lab_exists_with_node(window.api, candidate, node_name):
            return candidate

    mode = getattr(window, "_topology_mode", "master")
    attempted_text = ", ".join(attempted) if attempted else "none"
    if mode == "scenario":
        scenario = getattr(window, "current_scenario", None) or {}
        label = (
            f"Lab {scenario.get('id')} — {scenario.get('name')}"
            if scenario
            else "the selected scenario"
        )
        raise RuntimeError(
            f"No existing EVE-NG lab was found for {label}"
            + (f" containing node {node_name}" if node_name else "")
            + f". Checked: {attempted_text}. "
            "Create the scenario with 'CREATE FRESH SCENARIO LAB' first, "
            "then open the console again."
        )

    raise RuntimeError(
        "The Master Topology is currently a graphical definition, but no matching "
        "Master Lab exists on EVE-NG"
        + (f" containing node {node_name}" if node_name else "")
        + f". Checked: {attempted_text}. "
        "Build the Master Lab first, or switch Topology to CURRENT SCENARIO and "
        "open a device from a scenario lab that has already been created."
    )


def _install_resolved_connect_worker():
    original = TerminalSessionView._connect_worker
    if getattr(original, "_resolved_lab_target", False):
        return

    def connect_worker(view):
        try:
            workspace = getattr(view.window, "_console_workspace", None)
            if workspace is None:
                raise RuntimeError("Device Console workspace is not initialized.")
            lab = resolve_existing_lab(workspace, view.node_name)
            if lab != view.lab:
                view.window.log(
                    f"Interactive console target resolved: {view.lab or '<none>'} -> {lab}"
                )
                view.lab = lab
                view.after(0, lambda target=lab: view.backend_label.configure(text=target))
                view.after(
                    0,
                    lambda target=lab: view._append(
                        f"[Resolved existing EVE-NG lab: {target}]\n"
                    ),
                )
            return original(view)
        except Exception as exc:
            message = str(exc)
            view.window.log("ERROR: interactive console target: " + message)
            view.after(
                0,
                lambda msg=message: view._append(f"[Connection failed: {msg}]\n"),
            )
            view.after(0, lambda: view._set_status("● FAILED", view.window.DANGER))
            view.after(
                0,
                lambda msg=message: messagebox.showerror("Device Console", msg),
            )
            view._connecting = False
            return None

    connect_worker._resolved_lab_target = True
    TerminalSessionView._connect_worker = connect_worker


def install_console_target_compat(window):
    """Make console targets follow real EVE labs instead of predicted .unl paths."""
    _install_resolved_connect_worker()

    workspace = getattr(window, "_console_workspace", None)
    if workspace is None or getattr(workspace, "_target_compat_installed", False):
        return workspace

    original_target_lab = workspace._target_lab

    def target_lab(self, allow_unconnected=False):
        candidates = _candidate_labs(self)
        if candidates:
            return candidates[0]
        return original_target_lab(allow_unconnected)

    workspace._target_lab = types.MethodType(target_lab, workspace)
    workspace.resolve_existing_lab = types.MethodType(
        lambda self, node_name=None: resolve_existing_lab(self, node_name),
        workspace,
    )
    workspace._target_compat_installed = True

    try:
        window.winfo_toplevel().title("CCNA 200-301 EVE-NG Lab Builder v4.3.1")
    except tk.TclError:
        pass

    return workspace
