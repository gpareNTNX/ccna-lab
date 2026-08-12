import re
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

    def _console_port(self, lab, node_id):
        detail = self.api.node(lab, node_id).get("data", {})
        url = detail.get("url", "")
        match = re.search(r":(\d+)$", url)
        if not match:
            raise RuntimeError(f"No console port available for node {node_id}; is it running?")
        return int(match.group(1))

    def run_check(self, lab, check):
        nodes = self._node_map(lab)
        if check["node"] not in nodes:
            raise RuntimeError(f"Node {check['node']} not found.")
        node_id, _ = nodes[check["node"]]
        port = self._console_port(lab, node_id)
        channel = self.ssh.open_eve_console(port)
        console = CiscoConsole(channel)
        console.bootstrap()
        console.command("terminal length 0")
        output = console.command(check["command"], wait=1.8)
        channel.close()
        return self.validator.validate_output(check, output)

    def validate(self, lab, scenario):
        results = []
        for check in scenario.get("checks", []):
            self.log(f"{check['node']}: {check['command']}")
            results.append(self.run_check(lab, check))
        return results
