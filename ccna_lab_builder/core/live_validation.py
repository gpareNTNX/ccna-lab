import re
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

    def _node_map(self, lab):
        data = self.api.nodes(lab).get("data", {})
        return {v["name"]: (int(k), v) for k, v in data.items()}

    @staticmethod
    def _scenario_lab_name(scenario):
        slug = re.sub(r"[^A-Z0-9._-]+", "-", scenario["name"].upper()).strip("-")
        return f"CCNA-{scenario['id']}-{slug}.unl"

    def _resolve_lab(self, requested_lab, scenario):
        """Prefer the deterministic scenario lab over the Master Lab when it exists."""
        requested = str(requested_lab or "").strip()
        folder = requested.rsplit("/", 1)[0] if "/" in requested else ""
        scenario_name = self._scenario_lab_name(scenario)
        candidate = (folder.rstrip("/") + "/" + scenario_name) if folder else "/" + scenario_name

        current_name = requested.rsplit("/", 1)[-1]
        expected_prefix = f"CCNA-{scenario['id']}-"
        if current_name.startswith(expected_prefix):
            return requested

        try:
            self.api.get_lab(candidate)
        except RuntimeError:
            self.log(
                f"Validator target remains {requested}: scenario lab {candidate} was not found."
            )
            return requested

        self.log(
            f"Validator target adjusted from {requested} to scenario lab {candidate}."
        )
        return candidate

    @staticmethod
    def _native_backend_from_url(url):
        """Return a TCP backend only for a real native console URL."""
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
        """Backward-compatible helper retained for existing tests/callers."""
        backend = LiveValidator._native_backend_from_url(url)
        if not backend:
            return None
        return backend["host"], backend["port"]

    @staticmethod
    def _is_html5_url(url):
        return isinstance(url, str) and ("/html5/" in url or "/client/" in url)

    def _qemu_backend(self, node_info):
        if not self.ssh or not isinstance(node_info, dict):
            return None
        uuid = node_info.get("uuid")
        if not uuid:
            return None
        backend = self.ssh.discover_qemu_console(uuid)
        if backend:
            if backend["kind"] == "tcp":
                self.log(
                    f"QEMU console discovered for {node_info.get('name', uuid)}: "
                    f"{backend['host']}:{backend['port']}"
                )
            else:
                self.log(
                    f"QEMU UNIX console discovered for {node_info.get('name', uuid)}: "
                    f"{backend['path']}"
                )
        return backend

    def _api_tcp_backend_if_live(self, node_info):
        backend = self._native_backend_from_url(node_info.get("url"))
        if not backend:
            return None

        if not self.ssh:
            return backend

        listeners = self.ssh.console_listener_info(backend["port"])
        if listeners:
            return backend

        self.log(
            f"Ignoring stale EVE API console URL {backend['host']}:{backend['port']}: "
            "no TCP listener exists on the EVE-NG server."
        )
        return None

    def _console_backend(self, lab, node_id, node_info=None, attempts=15, delay=1.0):
        """Resolve a usable backend and start the node when necessary."""
        candidate = node_info or {}
        native_session_refreshed = False
        start_attempted = False
        start_error = None

        for attempt in range(1, attempts + 1):
            qemu_backend = self._qemu_backend(candidate)
            if qemu_backend:
                return qemu_backend

            api_backend = self._api_tcp_backend_if_live(candidate)
            if api_backend:
                return api_backend

            if not start_attempted:
                try:
                    self.log(
                        f"Node {node_id}: no running console backend found; "
                        "starting the scenario node via EVE-NG API..."
                    )
                    self.api.start_node(lab, node_id)
                    self.log(f"Node {node_id}: EVE-NG start request accepted.")
                except RuntimeError as exc:
                    start_error = str(exc)
                    self.log(
                        f"Node {node_id}: start request returned: {start_error}. "
                        "Continuing discovery in case the node is already starting."
                    )
                start_attempted = True

            if self._is_html5_url(candidate.get("url")) and not native_session_refreshed:
                self.api.login()
                native_session_refreshed = True

            nodes = self.api.nodes(lab).get("data", {})
            candidate = nodes.get(str(node_id), candidate)

            qemu_backend = self._qemu_backend(candidate)
            if qemu_backend:
                return qemu_backend

            api_backend = self._api_tcp_backend_if_live(candidate)
            if api_backend:
                return api_backend

            detail = self.api.node(lab, node_id).get("data", {})
            if detail:
                candidate = {**candidate, **detail}

            qemu_backend = self._qemu_backend(candidate)
            if qemu_backend:
                return qemu_backend

            api_backend = self._api_tcp_backend_if_live(candidate)
            if api_backend:
                return api_backend

            if attempt < attempts:
                if attempt == 1:
                    self.log(
                        f"Node {node_id}: waiting for EVE-NG/QEMU to create the console backend..."
                    )
                time.sleep(delay)

        status = candidate.get("status", "unknown")
        console = candidate.get("console", "unknown")
        url = candidate.get("url") or "none"
        uuid = candidate.get("uuid") or "none"
        extra = f" Start result: {start_error}" if start_error else ""
        raise RuntimeError(
            f"No usable console backend available for node {node_id} after {attempts} attempts. "
            f"EVE status={status}, console={console}, uuid={uuid}, url={url}. "
            "No matching QEMU serial backend or live native TCP listener was found."
            + extra
        )

    def _console_endpoint(self, lab, node_id, node_info=None, attempts=15, delay=1.0):
        """Backward-compatible native TCP endpoint helper."""
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
                f"{check['node']}: lab={lab}, node_id={node_id}, "
                f"uuid={node_info.get('uuid', 'unknown')}, prompt={prompt}"
            )
            console.command("terminal length 0", timeout=5.0)
            output = console.command(check["command"], timeout=8.0)
            result = self.validator.validate_output(check, output)
            context = (
                f"[Validator target] lab={lab}; node_id={node_id}; "
                f"uuid={node_info.get('uuid', 'unknown')}; prompt={prompt}; "
                f"backend={backend_label} ({backend.get('source', 'unknown')})"
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
        resolved_lab = self._resolve_lab(lab, scenario)
        self.log(f"Validation target: {resolved_lab}")
        results = []
        for check in scenario.get("checks", []):
            self.log(f"{check['node']}: {check['command']}")
            results.append(self.run_check(resolved_lab, check))
        return results
