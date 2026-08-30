"""Runtime-aware EVE-NG recovery for stale node and lab states."""

from __future__ import annotations

import shlex
import time
import types

from ccna_lab_builder.core.live_validation import LiveValidator


VERSION = "4.5.1"


def _node_status(node_info):
    try:
        return int((node_info or {}).get("status"))
    except (TypeError, ValueError):
        return None


def _refresh_node(validator, lab, node_id, fallback=None):
    candidate = dict(fallback or {})
    detail = {}
    try:
        detail = validator.api.node(lab, node_id).get("data", {})
        if isinstance(detail, dict):
            candidate.update(detail)
    except RuntimeError:
        pass

    if not detail:
        try:
            nodes = validator.api.nodes(lab).get("data", {})
            value = nodes.get(str(node_id), {})
            if isinstance(value, dict):
                candidate.update(value)
        except RuntimeError:
            pass
    return candidate


def _exact_backend(validator, node_id, node_info):
    runtime = validator._runtime_backend(node_id)
    if runtime:
        return runtime
    return validator._qemu_backend(node_info)


def _force_node_recycle(
    validator,
    lab,
    node_id,
    node_info,
    stop_wait=5.0,
    start_wait=20.0,
    poll=0.5,
):
    """Force one controlled stop/start and wait for the exact QEMU backend."""
    candidate = _refresh_node(validator, lab, node_id, node_info)
    validator.log(
        f"Node {node_id}: EVE reports status={candidate.get('status', 'unknown')} "
        "but no exact QEMU runtime is available; forcing a controlled restart..."
    )

    try:
        validator.api.stop_node(lab, node_id)
        validator.log(f"Node {node_id}: EVE-NG stop request accepted.")
    except RuntimeError as exc:
        validator.log(
            f"Node {node_id}: stop request returned {exc}; continuing stale-runtime recovery."
        )

    stop_deadline = time.monotonic() + max(0.0, stop_wait)
    while True:
        candidate = _refresh_node(validator, lab, node_id, candidate)
        backend = _exact_backend(validator, node_id, candidate)
        if not backend and _node_status(candidate) != 2:
            break
        if time.monotonic() >= stop_deadline:
            break
        time.sleep(max(0.01, poll))

    validator.api.start_node(lab, node_id)
    validator.log(f"Node {node_id}: EVE-NG restart request accepted; waiting for exact runtime...")

    start_deadline = time.monotonic() + max(0.0, start_wait)
    while True:
        candidate = _refresh_node(validator, lab, node_id, candidate)
        backend = _exact_backend(validator, node_id, candidate)
        if backend:
            validator.log(
                f"Node {node_id}: exact QEMU runtime recovered after controlled restart."
            )
            return backend, candidate
        if time.monotonic() >= start_deadline:
            break
        time.sleep(max(0.01, poll))

    validator.log(
        f"Node {node_id}: controlled restart completed but the exact QEMU runtime "
        "still did not appear."
    )
    return None, candidate


def _install_validator_recovery():
    original = LiveValidator._console_backend
    if getattr(original, "_stale_runtime_recovery", False):
        return

    def recovered(self, lab, node_id, node_info=None, attempts=15, delay=1.0):
        candidate = dict(node_info or {})

        if self.ssh:
            candidate = _refresh_node(self, lab, node_id, candidate)
            if _node_status(candidate) == 2 and not _exact_backend(self, node_id, candidate):
                backend, candidate = _force_node_recycle(
                    self,
                    lab,
                    node_id,
                    candidate,
                    poll=min(max(delay, 0.1), 0.5),
                )
                if backend:
                    return backend

        try:
            return original(
                self,
                lab,
                node_id,
                node_info=candidate,
                attempts=attempts,
                delay=delay,
            )
        except RuntimeError as exc:
            if not self.ssh or "No exact console backend available" not in str(exc):
                raise

            self.log(
                f"Node {node_id}: normal runtime discovery exhausted; performing one "
                "final controlled EVE node recycle."
            )
            backend, _candidate = _force_node_recycle(
                self,
                lab,
                node_id,
                candidate,
                poll=min(max(delay, 0.1), 0.5),
            )
            if backend:
                return backend
            raise RuntimeError(
                f"{exc} Controlled recovery also failed after stop/start. "
                "Check the IOSv image boot log and EVE-NG QEMU resources."
            ) from exc

    recovered._stale_runtime_recovery = True
    LiveValidator._console_backend = recovered


def _running_runtime_pids(controller, lab_uuid):
    if not lab_uuid or not controller.window.ssh:
        return []
    suffix = f"/{lab_uuid}/"
    script = (
        "target="
        + shlex.quote(suffix)
        + "; "
        + "for pid in $(pgrep -f 'qemu-system|qemu-kvm' 2>/dev/null); do "
        + 'cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null || true); '
        + 'case "$cwd" in /opt/unetlab/tmp/*"$target"*) printf "%s\\n" "$pid";; esac; '
        + "done"
    )
    out, _err = controller.window.ssh.exec(script)
    return [line.strip() for line in out.splitlines() if line.strip().isdigit()]


def _lab_uuid(controller, lab):
    try:
        data = controller.window.api.get_lab(lab).get("data", {})
    except RuntimeError:
        return ""
    return str(data.get("id") or "").strip()


def _wait_for_lab_runtimes_to_stop(controller, lab, lab_uuid, timeout=10.0, poll=0.25):
    if not lab_uuid:
        return True
    deadline = time.monotonic() + max(0.0, timeout)
    last_pids = []
    while True:
        last_pids = _running_runtime_pids(controller, lab_uuid)
        if not last_pids:
            controller.window.log(f"Confirmed all QEMU runtimes stopped: {lab}")
            return True
        if time.monotonic() >= deadline:
            controller.window.log(
                f"ERROR: QEMU runtimes still active for {lab}: {', '.join(last_pids)}"
            )
            return False
        time.sleep(max(0.01, poll))


def _install_single_lab_runtime_wait(controller):
    original = controller._stop_lab
    if getattr(original, "_runtime_wait", False):
        return

    def stop_lab(self, lab):
        lab_uuid = _lab_uuid(self, lab)
        result = original(lab)
        if lab_uuid and self.window.ssh:
            self.window.log(
                f"Waiting for EVE-NG QEMU runtimes to stop before leaving {lab}..."
            )
            if not _wait_for_lab_runtimes_to_stop(self, lab, lab_uuid):
                raise RuntimeError(
                    f"EVE-NG accepted the stop request for {lab}, but QEMU processes "
                    "are still running. The lab switch was aborted."
                )
        return result

    stop_lab._runtime_wait = True
    controller._stop_lab = types.MethodType(stop_lab, controller)


def install_runtime_recovery(window):
    """Install stale-runtime repair and strict stop confirmation for lab swaps."""
    _install_validator_recovery()

    controller = getattr(window, "_active_lab_controller", None)
    if controller is not None:
        _install_single_lab_runtime_wait(controller)

    window._runtime_recovery_installed = True
    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except Exception:
        pass
    return controller
