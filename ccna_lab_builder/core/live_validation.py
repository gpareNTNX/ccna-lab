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
    def _native_endpoint_from_url(url):
        """Return (host, port) only for a real native console URL.

        HTML5/Guacamole client identifiers are not raw Telnet ports and must
        never be opened directly through SSH port forwarding.
        """
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
        return parsed.hostname, parsed.port

    @staticmethod
    def _is_html5_url(url):
        return isinstance(url, str) and ("/html5/" in url or "/client/" in url)

    def _console_endpoint(self, lab, node_id, node_info=None, attempts=12, delay=1.0):
        """Return EVE-NG's raw native console endpoint for a node."""
        candidate = node_info or {}
        native_session_refreshed = False

        for attempt in range(1, attempts + 1):
            url = candidate.get("url")
            endpoint = self._native_endpoint_from_url(url)
            if endpoint:
                return endpoint

            if self._is_html5_url(url) and not native_session_refreshed:
                self.log(
                    f"Node {node_id}: HTML5 console URL detected; "
                    "requesting native EVE-NG console mode..."
                )
                self.api.login()
                native_session_refreshed = True

            nodes = self.api.nodes(lab).get("data", {})
            candidate = nodes.get(str(node_id), {})
            endpoint = self._native_endpoint_from_url(candidate.get("url"))
            if endpoint:
                return endpoint

            detail = self.api.node(lab, node_id).get("data", {})
            endpoint = self._native_endpoint_from_url(detail.get("url"))
            if endpoint:
                return endpoint

            if attempt < attempts:
                if attempt == 1:
                    self.log(
                        f"Node {node_id}: waiting for EVE-NG to expose a native console port..."
                    )
                time.sleep(delay)

        status = candidate.get("status", "unknown")
        console = candidate.get("console", "unknown")
        url = candidate.get("url") or "none"
        raise RuntimeError(
            f"No native console endpoint available for node {node_id} after {attempts} attempts. "
            f"EVE status={status}, console={console}, url={url}. "
            "The validator requires EVE-NG native console mode, not an HTML5/Guacamole client URL."
        )

    def run_check(self, lab, check):
        nodes = self._node_map(lab)
        if check["node"] not in nodes:
            raise RuntimeError(f"Node {check['node']} not found.")

        node_id, node_info = nodes[check["node"]]
        host, port = self._console_endpoint(lab, node_id, node_info=node_info)
        self.log(f"{check['node']}: native console {host}:{port}")

        channel = self.ssh.open_eve_console(port, target_host=host)
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
