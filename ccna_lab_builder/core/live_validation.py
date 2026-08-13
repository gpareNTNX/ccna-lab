import shlex
import time
from urllib.parse import urlparse

from ccna_lab_builder.core.ssh import CiscoConsole
from ccna_lab_builder.core.validator import Validator


class LiveValidator:
    def __init__(self, api, ssh, log=print):
        self.api = api
        self.ssh = ssh
        self.log = log
        self.validator = Validator()
        self._active_lab_uuid = "unknown"
        self._runtime_note = ""

    def _node_map(self, lab):
        data = self.api.nodes(lab).get("data", {})
        return {v["name"]: (int(k), v) for k, v in data.items()}

    @staticmethod
    def _native_backend_from_url(url):
        if not isinstance(url, str):
            return None
        value = url.strip()
        if not value or "/html5/" in value or "/client/" in value:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"telnet", "tcp"} or not parsed.hostname or not parsed.port:
            return None
        if not 1 <= parsed.port <= 65535:
            return None
        return {
            "kind": "tcp",
            "host": parsed.hostname,
            "port": parsed.port,
            "source": "eve-api",
        }

    @staticmethod
    def _native_endpoint_from_url(url):
        backend = LiveValidator._native_backend_from_url(url)
        if not backend:
            return None
        return backend["host"], backend["port"]

    @staticmethod
    def _is_html5_url(url):
        return isinstance(url, str) and ("/html5/" in url or "/client/" in url)

    def _runtime_backend(self, node_id):
        """Resolve QEMU by EVE's exact POD/LAB_UUID/NODE_ID runtime directory."""
        if not self.ssh:
            return None
        lab_uuid = str(self._active_lab_uuid or "").strip()
        if not lab_uuid or lab_uuid == "unknown":
            return None

        suffix = f"/{lab_uuid}/{int(node_id)}"
        script = (
            "target_suffix="
            + shlex.quote(suffix)
            + "; "
            + "for pid in $(pgrep -f 'qemu-system|qemu-kvm' 2>/dev/null); do "
            + 'cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null || true); '
            + 'case "$cwd" in /opt/unetlab/tmp/*"$target_suffix") '
            + 'printf "__PID__=%s\\n" "$pid"; '
            + 'printf "__CWD__=%s\\n" "$cwd"; '
            + 'tr "\\000" " " < "/proc/$pid/cmdline" 2>/dev/null; '
            + 'printf "\\n"; exit 0;; esac; done'
        )
        out, err = self.ssh.exec(script)
        lines = [line for line in out.splitlines() if line.strip()]
        if not lines:
            self._runtime_note = (
                f"No QEMU process cwd matched /opt/unetlab/tmp/*{suffix}. "
                f"stderr={err.strip() or 'none'}"
            )
            return None

        pid = ""
        runtime_dir = ""
        command_lines = []
        for line in lines:
            if line.startswith("__PID__="):
                pid = line.split("=", 1)[1].strip()
            elif line.startswith("__CWD__="):
                runtime_dir = line.split("=", 1)[1].strip()
            else:
                command_lines.append(line)

        qemu_command = " ".join(command_lines).strip()
        backend = self.ssh.parse_qemu_console_backend(qemu_command)
        if not backend:
            sample = qemu_command[:700] if qemu_command else "<empty qemu command>"
            self._runtime_note = (
                f"Matched runtime {runtime_dir or suffix} pid={pid or 'unknown'}, "
                f"but no supported serial backend was parsed. QEMU: {sample}"
            )
            return None

        backend.update(
            {
                "source": "eve-runtime",
                "lab_uuid": lab_uuid,
                "node_id": int(node_id),
                "pid": pid or "unknown",
                "runtime_dir": runtime_dir or f"/opt/unetlab/tmp/*{suffix}",
            }
        )
        self._runtime_note = ""
        label = (
            f"{backend['host']}:{backend['port']}"
            if backend["kind"] == "tcp"
            else backend["path"]
        )
        self.log(
            f"EVE runtime console matched lab_uuid={lab_uuid}, node_id={node_id}, "
            f"pid={backend['pid']}: {label}"
        )
        return backend

    def _qemu_backend(self, node_info):
        """Secondary fallback when a build puts the node UUID in QEMU args."""
        if not self.ssh or not isinstance(node_info, dict):
            return None
        uuid = node_info.get("uuid")
        if not uuid:
            return None
        backend = self.ssh.discover_qemu_console(uuid)
        if backend:
            backend["source"] = "qemu-node-uuid"
        return backend

    def _api_backend_diagnostic(self, node_info):
        backend = self._native_backend_from_url(node_info.get("url"))
        if not backend or not self.ssh:
            return
        listeners = self.ssh.console_listener_info(backend["port"])
        if listeners:
            self.log(
                f"EVE API advertises {backend['host']}:{backend['port']} and a listener exists, "
                "but it will not be used without a matching EVE runtime process."
            )
        else:
            self.log(
                f"Ignoring stale EVE API console URL {backend['host']}:{backend['port']}: "
                "no TCP listener exists on the EVE-NG server."
            )

    def _console_backend(self, lab, node_id, node_info=None, attempts=15, delay=1.0):
        candidate = node_info or {}
        native_session_refreshed = False
        start_attempted = False
        start_error = None

        for attempt in range(1, attempts + 1):
            runtime = self._runtime_backend(node_id)
            if runtime:
                return runtime

            qemu = self._qemu_backend(candidate)
            if qemu:
                return qemu

            if not self.ssh:
                api_backend = self._native_backend_from_url(candidate.get("url"))
                if api_backend:
                    return api_backend
            else:
                self._api_backend_diagnostic(candidate)

            if not start_attempted:
                try:
                    self.log(
                        f"Node {node_id}: no exact runtime console found; "
                        "starting the selected lab node via EVE-NG API..."
                    )
                    self.api.start_node(lab, node_id)
                    self.log(f"Node {node_id}: EVE-NG start request accepted.")
                except RuntimeError as exc:
                    start_error = str(exc)
                    self.log(
                        f"Node {node_id}: start request returned: {start_error}. "
                        "Continuing exact runtime discovery."
                    )
                start_attempted = True

            if (
                not self.ssh
                and self._is_html5_url(candidate.get("url"))
                and not native_session_refreshed
            ):
                self.api.login()
                native_session_refreshed = True

            nodes = self.api.nodes(lab).get("data", {})
            candidate = nodes.get(str(node_id), candidate)

            runtime = self._runtime_backend(node_id)
            if runtime:
                return runtime

            qemu = self._qemu_backend(candidate)
            if qemu:
                return qemu

            if not self.ssh:
                api_backend = self._native_backend_from_url(candidate.get("url"))
                if api_backend:
                    return api_backend

            detail = self.api.node(lab, node_id).get("data", {})
            if detail:
                candidate = {**candidate, **detail}

            runtime = self._runtime_backend(node_id)
            if runtime:
                return runtime

            qemu = self._qemu_backend(candidate)
            if qemu:
                return qemu

            if not self.ssh:
                api_backend = self._native_backend_from_url(candidate.get("url"))
                if api_backend:
                    return api_backend

            if attempt < attempts:
                if attempt == 1:
                    self.log(
                        f"Node {node_id}: waiting for the exact EVE runtime/QEMU console..."
                    )
                time.sleep(delay)

        status = candidate.get("status", "unknown")
        console = candidate.get("console", "unknown")
        url = candidate.get("url") or "none"
        uuid = candidate.get("uuid") or "none"
        extra = f" Start result: {start_error}" if start_error else ""
        runtime_note = (
            f" Runtime diagnostic: {self._runtime_note}" if self._runtime_note else ""
        )
        raise RuntimeError(
            f"No exact console backend available for node {node_id} after {attempts} attempts. "
            f"lab_uuid={self._active_lab_uuid}, EVE status={status}, console={console}, "
            f"node_uuid={uuid}, api_url={url}. "
            "The validator refused to use an unverified EVE API console port."
            + runtime_note
            + extra
        )

    def _console_endpoint(self, lab, node_id, node_info=None, attempts=15, delay=1.0):
        backend = self._console_backend(
            lab, node_id, node_info=node_info, attempts=attempts, delay=delay
        )
        if backend.get("kind") != "tcp":
            raise RuntimeError(
                f"Console backend for node {node_id} is {backend.get('kind')}, not TCP."
            )
        return backend["host"], backend["port"]

    def run_check(self, lab, check):
        nodes = self._node_map(lab)
        if check["node"] not in nodes:
            raise RuntimeError(f"Node {check['node']} not found in {lab}.")

        node_id, node_info = nodes[check["node"]]
        backend = self._console_backend(lab, node_id, node_info=node_info)
        if backend["kind"] == "tcp":
            backend_label = f"{backend['host']}:{backend['port']}"
        else:
            backend_label = backend["path"]
        self.log(
            f"{check['node']}: console {backend_label} "
            f"({backend.get('source', 'unknown')})"
        )

        channel = self.ssh.open_console_backend(backend)
        try:
            console = CiscoConsole(channel)
            console.bootstrap()
            prompt = console.ensure_privileged(timeout=5.0)
            self.log(
                f"{check['node']}: lab={lab}, lab_uuid={self._active_lab_uuid}, "
                f"node_id={node_id}, uuid={node_info.get('uuid', 'unknown')}, prompt={prompt}"
            )
            console.command("terminal length 0", timeout=5.0)
            output = console.command(check["command"], timeout=8.0)
            result = self.validator.validate_output(check, output)
            context = (
                f"[Validator target] lab={lab}; lab_uuid={self._active_lab_uuid}; "
                f"node_id={node_id}; uuid={node_info.get('uuid', 'unknown')}; "
                f"prompt={prompt}; backend={backend_label} "
                f"({backend.get('source', 'unknown')}); "
                f"pid={backend.get('pid', 'n/a')}; "
                f"runtime={backend.get('runtime_dir', 'n/a')}"
            )
            result.output = context + ("\n" + result.output if result.output else "")
            if result.passed:
                self.log(f"{check['node']}: validation PASS")
            else:
                self.log(
                    f"{check['node']}: validation FAIL; missing: "
                    + ", ".join(result.missing)
                )
            return result
        finally:
            channel.close()

    def validate(self, lab, scenario):
        target_lab = str(lab or "").strip()
        if not target_lab:
            raise RuntimeError("Select an EVE-NG lab to validate.")

        lab_data = self.api.get_lab(target_lab).get("data", {})
        self._active_lab_uuid = str(lab_data.get("id") or "unknown")
        self.log(
            f"Validation target (exact): {target_lab}; "
            f"lab_uuid={self._active_lab_uuid}"
        )

        results = []
        for check in scenario.get("checks", []):
            self.log(f"{check['node']}: {check['command']}")
            results.append(self.run_check(target_lab, check))
        return results
