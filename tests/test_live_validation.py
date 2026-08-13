import unittest

from ccna_lab_builder.core.live_validation import LiveValidator
from ccna_lab_builder.core.ssh import SSHConnection


class FakeAPI:
    def __init__(self):
        self.nodes_calls = 0
        self.node_calls = 0
        self.login_calls = 0
        self.start_calls = 0

    def login(self):
        self.login_calls += 1
        return {"status": "success"}

    def start_node(self, _lab, _node_id):
        self.start_calls += 1
        return {"status": "success", "message": "Node started"}

    def nodes(self, _lab):
        self.nodes_calls += 1
        return {
            "data": {
                "1": {
                    "name": "R1-EDGE",
                    "console": "telnet",
                    "url": "telnet://172.16.200.156:32769",
                    "uuid": "11111111-1111-1111-1111-111111111111",
                    "type": "qemu",
                }
            }
        }

    def node(self, _lab, _node_id):
        self.node_calls += 1
        return {"data": {}}


class RuntimeSSH:
    def __init__(self, runtime_output, listeners=None):
        self.runtime_output = runtime_output
        self.listeners = list(listeners or [])
        self.exec_calls = []
        self.uuid_calls = []

    def exec(self, command):
        self.exec_calls.append(command)
        return self.runtime_output, ""

    @staticmethod
    def parse_qemu_console_backend(command):
        return SSHConnection.parse_qemu_console_backend(command)

    def discover_qemu_console(self, uuid):
        self.uuid_calls.append(uuid)
        return None

    def console_listener_info(self, _port):
        return list(self.listeners)


class LiveValidationConsoleTests(unittest.TestCase):
    def test_native_endpoint_from_telnet_url(self):
        self.assertEqual(
            LiveValidator._native_endpoint_from_url(
                "telnet://172.16.200.156:32769"
            ),
            ("172.16.200.156", 32769),
        )

    def test_html5_guacamole_url_is_not_treated_as_telnet_port(self):
        url = (
            "/html5/#/client/MzI3NjkAYwBteXNxbA=="
            "?token=F1666351184206978A3B4C5A78E5DA6225CA557FDEDCC7199962BB1537961091"
        )
        self.assertIsNone(LiveValidator._native_endpoint_from_url(url))

    def test_api_console_remains_available_for_api_only_callers(self):
        api = FakeAPI()
        validator = LiveValidator(api, ssh=None)
        node_info = api.nodes("/lab.unl")["data"]["1"]

        endpoint = validator._console_endpoint(
            "/lab.unl", 1, node_info=node_info, attempts=1, delay=0
        )

        self.assertEqual(endpoint, ("172.16.200.156", 32769))

    def test_exact_eve_runtime_wins_over_listening_but_wrong_api_port(self):
        api = FakeAPI()
        ssh = RuntimeSSH(
            "__PID__=4242\n"
            "__CWD__=/opt/unetlab/tmp/0/lab-uuid-123/1\n"
            "/opt/qemu/bin/qemu-system-x86_64 "
            "-serial telnet:127.0.0.1:40001,server,nowait "
            "-drive file=virtioa.qcow2\n",
            listeners=["0.0.0.0:32769"],
        )
        logs = []
        validator = LiveValidator(api, ssh=ssh, log=logs.append)
        validator._active_lab_uuid = "lab-uuid-123"
        node_info = api.nodes("/lab.unl")["data"]["1"]

        backend = validator._console_backend(
            "/lab.unl", 1, node_info=node_info, attempts=1, delay=0
        )

        self.assertEqual(backend["source"], "eve-runtime")
        self.assertEqual(backend["port"], 40001)
        self.assertEqual(backend["pid"], "4242")
        self.assertEqual(
            backend["runtime_dir"],
            "/opt/unetlab/tmp/0/lab-uuid-123/1",
        )
        self.assertEqual(api.start_calls, 0)
        self.assertTrue(any("lab-uuid-123" in call for call in ssh.exec_calls))

    def test_validator_refuses_unverified_api_port_when_runtime_does_not_match(self):
        api = FakeAPI()
        ssh = RuntimeSSH("", listeners=["0.0.0.0:32769"])
        validator = LiveValidator(api, ssh=ssh, log=lambda _message: None)
        validator._active_lab_uuid = "lab-uuid-123"
        node_info = api.nodes("/lab.unl")["data"]["1"]

        with self.assertRaisesRegex(RuntimeError, "refused to use an unverified"):
            validator._console_backend(
                "/lab.unl", 1, node_info=node_info, attempts=1, delay=0
            )

        self.assertEqual(api.start_calls, 1)


if __name__ == "__main__":
    unittest.main()
