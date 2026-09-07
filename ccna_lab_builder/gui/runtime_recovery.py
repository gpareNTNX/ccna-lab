"""Runtime-aware EVE-NG recovery for stale node and lab states."""

from __future__ import annotations

import shlex
import time
import types

from ccna_lab_builder.core.live_validation import LiveValidator


VERSION = "5.1.2"
GRACEFUL_LAB_STOP_TIMEOUT = 30.0
INDIVIDUAL_NODE_STOP_TIMEOUT = 15.0
SIGTERM_TIMEOUT = 8.0
SIGKILL_TIMEOUT = 5.0
LAB_STOP_POLL = 0.25


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


def _signal_lab_runtimes(controller, lab_uuid, signal):
    """Signal only QEMU PIDs whose runtime cwd belongs to the exact EVE lab UUID."""
    signal = str(signal or "").upper().strip()
    if signal not in {"TERM", "KILL"}:
        raise ValueError("Only TERM and KILL are allowed for scoped QEMU recovery.")
    if not lab_uuid or not controller.window.ssh:
        return []

    suffix = f"/{lab_uuid}/"
    script = (
        "target="
        + shlex.quote(suffix)
        + "; sig="
        + shlex.quote(signal)
        + "; "
        + "for pid in $(pgrep -f 'qemu-system|qemu-kvm' 2>/dev/null); do "
        + 'cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null || true); '
        + 'case "$cwd" in /opt/unetlab/tmp/*"$target"*) '
        + 'kill -s "$sig" "$pid" 2>/dev/null && printf "%s\\n" "$pid";; esac; '
        + "done"
    )
    out, err = controller.window.ssh.exec(script)
    signaled = [line.strip() for line in out.splitlines() if line.strip().isdigit()]
    if signaled:
        controller.window.log(
            f"Sent SIG{signal} to {len(signaled)} QEMU runtime(s) scoped to "
            f"EVE lab UUID {lab_uuid}: {', '.join(signaled)}"
        )
    if err.strip():
        controller.window.log(f"WARNING: scoped SIG{signal} command: {err.strip()}")
    return signaled


def _lab_uuid(controller, lab):
    try:
        data = controller.window.api.get_lab(lab).get("data", {})
    except RuntimeError:
        return ""
    return str(data.get("id") or "").strip()


def _lab_node_ids(controller, lab):
    try:
        data = controller.window.api.nodes(lab).get("data", {})
    except RuntimeError as exc:
        controller.window.log(f"WARNING: could not enumerate EVE nodes for {lab}: {exc}")
        return []

    if isinstance(data, dict):
        return [str(node_id) for node_id in data.keys()]
    if isinstance(data, list):
        node_ids = []
        for node in data:
            if isinstance(node, dict) and node.get("id") is not None:
                node_ids.append(str(node["id"]))
        return node_ids
    return []


def _stop_lab_nodes_individually(controller, lab):
    node_ids = _lab_node_ids(controller, lab)
    if not node_ids:
        controller.window.log(f"No EVE node IDs were available for per-node stop retry: {lab}")
        return 0

    controller.window.log(
        f"Retrying stop individually for {len(node_ids)} node(s) in {lab}..."
    )
    accepted = 0
    for node_id in node_ids:
        try:
            controller.window.api.stop_node(lab, node_id)
            accepted += 1
        except RuntimeError as exc:
            controller.window.log(
                f"WARNING: EVE-NG did not accept stop for node {node_id} in {lab}: {exc}"
            )
    controller.window.log(
        f"Per-node stop requests accepted for {accepted}/{len(node_ids)} node(s): {lab}"
    )
    return accepted


def _wait_for_lab_runtimes_to_stop(
    controller,
    lab,
    lab_uuid,
    timeout=GRACEFUL_LAB_STOP_TIMEOUT,
    poll=LAB_STOP_POLL,
    log_timeout=True,
):
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
            if log_timeout:
                controller.window.log(
                    f"QEMU runtimes still active for {lab}: {', '.join(last_pids)}"
                )
            return False
        time.sleep(max(0.01, poll))


def _recover_stuck_lab_runtimes(
    controller,
    lab,
    lab_uuid,
    graceful_timeout=GRACEFUL_LAB_STOP_TIMEOUT,
    node_timeout=INDIVIDUAL_NODE_STOP_TIMEOUT,
    term_timeout=SIGTERM_TIMEOUT,
    kill_timeout=SIGKILL_TIMEOUT,
    poll=LAB_STOP_POLL,
):
    """Escalate a stuck EVE lab stop without touching QEMU processes from other labs."""
    controller.window.log(
        f"Waiting up to {graceful_timeout:g}s for EVE-NG QEMU runtimes to stop: {lab}"
    )
    if _wait_for_lab_runtimes_to_stop(
        controller,
        lab,
        lab_uuid,
        timeout=graceful_timeout,
        poll=poll,
        log_timeout=False,
    ):
        return True

    controller.window.log(
        f"WARNING: graceful lab stop exceeded {graceful_timeout:g}s for {lab}; "
        "retrying with individual node stops."
    )
    _stop_lab_nodes_individually(controller, lab)
    if _wait_for_lab_runtimes_to_stop(
        controller,
        lab,
        lab_uuid,
        timeout=node_timeout,
        poll=poll,
        log_timeout=False,
    ):
        return True

    remaining = _running_runtime_pids(controller, lab_uuid)
    controller.window.log(
        f"WARNING: {len(remaining)} QEMU runtime(s) are still attached to {lab}; "
        "sending SIGTERM only to processes scoped to this lab UUID."
    )
    _signal_lab_runtimes(controller, lab_uuid, "TERM")
    if _wait_for_lab_runtimes_to_stop(
        controller,
        lab,
        lab_uuid,
        timeout=term_timeout,
        poll=poll,
        log_timeout=False,
    ):
        return True

    remaining = _running_runtime_pids(controller, lab_uuid)
    controller.window.log(
        f"WARNING: {len(remaining)} QEMU runtime(s) ignored SIGTERM for {lab}; "
        "sending scoped SIGKILL as the final recovery step."
    )
    _signal_lab_runtimes(controller, lab_uuid, "KILL")
    if _wait_for_lab_runtimes_to_stop(
        controller,
        lab,
        lab_uuid,
        timeout=kill_timeout,
        poll=poll,
        log_timeout=False,
    ):
        return True

    remaining = _running_runtime_pids(controller, lab_uuid)
    controller.window.log(
        f"ERROR: QEMU runtimes could not be stopped for {lab}: {', '.join(remaining) or 'unknown'}"
    )
    return False


def _install_single_lab_runtime_wait(controller):
    original = controller._stop_lab
    if getattr(original, "_runtime_wait", False):
        return

    def stop_lab(self, lab):
        lab_uuid = _lab_uuid(self, lab)
        result = original(lab)
        if lab_uuid and self.window.ssh:
            if not _recover_stuck_lab_runtimes(self, lab, lab_uuid):
                raise RuntimeError(
                    f"EVE-NG accepted the stop request for {lab}, but its QEMU processes "
                    "could not be terminated after graceful stop, per-node stop, SIGTERM, "
                    "and lab-scoped SIGKILL recovery. The lab switch was aborted."
                )
        return result

    stop_lab._runtime_wait = True
    controller._stop_lab = types.MethodType(stop_lab, controller)


def install_runtime_recovery(window):
    """Install stale-runtime repair and robust stop confirmation for lab swaps."""
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
