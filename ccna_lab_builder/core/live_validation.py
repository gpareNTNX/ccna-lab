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

    def _console_backend(self, lab, node_id, node_info=None, attempts=6, delay=1.0):
        """Resolve a usable console backend from EVE API or the QEMU process."""
        candidate = node_info or {}
        native_session_refreshed = False

        for attempt in range(1, attempts + 1):
            backend = self._native_backend_from_url(candidate.get("url"))
            if backend:
                return backend

            # HTML5 URLs contain a Guacamole/MySQL connection identifier, not
            # a raw Telnet port. Inspect the running QEMU process instead.
            qemu_backend = self._qemu_backend(candidate)
            if qemu_backend:
                return qemu_backend

            if self._is_html5_url(candidate.get("url")) and not native_session_refreshed:
                self.log(
                    f"Node {node_id}: HTML5 console URL detected; "
                    "requesting native EVE-NG console mode..."
                )
                self.api.login()
                native_session_refreshed = True

            nodes = self.api.nodes(lab).get("data", {})
            candidate = nodes.get(str(node_id), candidate)
            backend = self._native_backend_from_url(candidate.get("url"))
            if backend:
                return backend

            qemu_backend = self._qemu_backend(candidate)
            if qemu_backend:
                return qemu_backend

            detail = self.api.node(lab, node_id).get("data", {})
            backend = self._native_backend_from_url(detail.get("url"))
            if backend:
                return backend

            qemu_backend = self._qemu_backend(detail)
            if qemu_backend:
                return qemu_backend

            if attempt < attempts:
                if attempt == 1:
                    self.log(
                        f"Node {node_id}: waiting for EVE-NG/QEMU console backend..."
                    )
                time.sleep(delay)

        status = candidate.get("status", "unknown")
        console = candidate.get("console", "unknown")
        url = candidate.get("url") or "none"
        uuid = candidate.get("uuid") or "none"
        raise RuntimeError(
            f"No usable console backend available for node {node_id} after {attempts} attempts. "
            f"EVE status={status}, console={console}, uuid={uuid}, url={url}. "
            "The API did not expose a native console and no matching QEMU serial backend was found."
        )

    def _console_endpoint(self, lab, node_id, node_info=None, attempts=6, delay=1.0):
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
            raise RuntimeError(f"Node {check['node']} not found.")

        node_id, node_info = nodes[check["node"]]
        backend = self._console_backend(lab, node_id, node_info=node_info)
        if backend["kind"] == "tcp":
            self.log(
                f"{check['node']}: console {backend['host']}:{backend['port']} "
                f"({backend.get('source', 'unknown')})"
            )
        else:
            self.log(
                f"{check['node']}: console {backend['path']} "
                f"({backend.get('source', 'unknown')})"
            )

        channel = self.ssh.open_console_backend(backend)
        try:
            console = CiscoConsole(channel)
            console.bootstrap()
            console.command("terminal length 0")
            output = console.command(check["command"], wait=1.8)
            return self.validator.validate_output(check, output)
        finally:
            channel.close()

    def validate(self, lab, scenario):
        results = []
        for check in scenario.get("checks", []):
            self.log(f"{check['node']}: {check['command']}")
            results.append(self.run_check(lab, check))
        return results
