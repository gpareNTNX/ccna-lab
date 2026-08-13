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
        if not isinstance(url, str):
            return None
        match = re.search(r":(\d+)/?$", url.strip())
        return int(match.group(1)) if match else None

    def _console_port(self, lab, node_id, node_info=None, attempts=12, delay=1.0):
        """Return EVE-NG's dynamic native-console port for a node.

        Recent EVE-NG releases expose the dynamic console URL on the *node list*
        response. Some builds do not expose the same URL consistently on the
        single-node endpoint, so always prefer the list data and use the detail
        endpoint only as a fallback.
        """
        candidate = node_info or {}

        for attempt in range(1, attempts + 1):
            port = self._port_from_url(candidate.get("url"))
            if port:
                return port

            # Refresh the node list first: this is where current EVE-NG builds
            # expose dynamic native-console URLs such as telnet://127.0.0.1:32769.
            nodes = self.api.nodes(lab).get("data", {})
            candidate = nodes.get(str(node_id), {})
            port = self._port_from_url(candidate.get("url"))
            if port:
                return port

            # Compatibility fallback for older EVE-NG builds.
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
            "Make sure the node is started and has finished launching in EVE-NG."
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
