import base64
import re
import time

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
    def _port_from_url(url):
        """Extract the dynamic EVE-NG console port from native or HTML5 URLs.

        Native console examples use ``telnet://127.0.0.1:32769``.
        Current HTML5/Guacamole URLs can look like
        ``/html5/#/client/MzI3NjkAYwBteXNxbA==?token=...``. The client token
        is base64-encoded Guacamole connection data whose first NUL-delimited
        field is the dynamic console port (``32769\0c\0mysql`` in this example).
        """
        if not isinstance(url, str):
            return None

        value = url.strip()

        # Native EVE-NG console URL.
        match = re.search(r":(\d+)/?$", value)
        if match:
            port = int(match.group(1))
            return port if 1 <= port <= 65535 else None

        # HTML5 / Guacamole console URL.
        match = re.search(r"/client/([^/?#]+)", value)
        if not match:
            return None

        encoded = match.group(1)
        try:
            padded = encoded + "=" * (-len(encoded) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
            first_field = decoded.split(b"\x00", 1)[0].decode("ascii")
            if not first_field.isdigit():
                return None
            port = int(first_field)
            return port if 1 <= port <= 65535 else None
        except (ValueError, UnicodeDecodeError, base64.binascii.Error):
            return None

    def _console_port(self, lab, node_id, node_info=None, attempts=12, delay=1.0):
        """Return EVE-NG's dynamic native-console port for a node.

        EVE-NG can expose either a native telnet URL or an HTML5/Guacamole URL.
        Prefer the node-list data, because recent builds expose the current
        dynamic console information there, and use the single-node endpoint as
        a compatibility fallback.
        """
        candidate = node_info or {}

        for attempt in range(1, attempts + 1):
            port = self._port_from_url(candidate.get("url"))
            if port:
                return port

            nodes = self.api.nodes(lab).get("data", {})
            candidate = nodes.get(str(node_id), {})
            port = self._port_from_url(candidate.get("url"))
            if port:
                return port

            detail = self.api.node(lab, node_id).get("data", {})
            port = self._port_from_url(detail.get("url"))
            if port:
                return port

            if attempt < attempts:
                if attempt == 1:
                    self.log(
                        f"Node {node_id}: waiting for EVE-NG to assign a console port..."
                    )
                time.sleep(delay)

        status = candidate.get("status", "unknown")
        console = candidate.get("console", "unknown")
        url = candidate.get("url") or "none"
        raise RuntimeError(
            f"No console port available for node {node_id} after {attempts} attempts. "
            f"EVE status={status}, console={console}, url={url}. "
            "Make sure EVE-NG exposes a supported native or HTML5 console URL."
        )

    def run_check(self, lab, check):
        nodes = self._node_map(lab)
        if check["node"] not in nodes:
            raise RuntimeError(f"Node {check['node']} not found.")

        node_id, node_info = nodes[check["node"]]
        port = self._console_port(lab, node_id, node_info=node_info)
        self.log(f"{check['node']}: console port {port}")

        channel = self.ssh.open_eve_console(port)
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
