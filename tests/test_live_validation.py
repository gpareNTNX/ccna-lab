import unittest

from ccna_lab_builder.core.live_validation import LiveValidator


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
                    "url": "telnet://127.0.0.1:32769",
                    "uuid": "11111111-1111-1111-1111-111111111111",
                    "type": "qemu",
                }
            }
        }

    def node(self, _lab, _node_id):
        self.node_calls += 1
        return {"data": {}}


class DelayedAPI(FakeAPI):
    def nodes(self, _lab):
        self.nodes_calls += 1
        url = "" if self.nodes_calls < 2 else "telnet://127.0.0.1:32770"
        return {
            "data": {
                "1": {
                    "name": "R1-EDGE",
                    "console": "telnet",
                    "url": url,
                    "uuid": "11111111-1111-1111-1111-111111111111",
                    "type": "qemu",
                }
            }
        }


class HTML5ThenNativeAPI(FakeAPI):
    def nodes(self, _lab):
        self.nodes_calls += 1
        if self.login_calls:
            url = "telnet://127.0.0.1:32771"
        else:
            url = (
                "/html5/#/client/MzI3NjkAYwBteXNxbA=="
                "?token=F1666351184206978A3B4C5A78E5DA6225CA557FDEDCC7199962BB1537961091"
            )
        return {
            "data": {
                "1": {
                    "name": "R1-EDGE",
                    "console": "telnet",
                    "url": url,
                    "uuid": "11111111-1111-1111-1111-111111111111",
                    "type": "qemu",
                }
            }
        }


class PersistentHTML5API(FakeAPI):
    def nodes(self, _lab):
        self.nodes_calls += 1
        return {
            "data": {
                "1": {
                    "name": "R1-EDGE",
                    "console": "telnet",
                    "url": "/html5/#/client/MzI3NjkAYwBteXNxbA==?token=ABC",
                    "uuid": "22222222-2222-2222-2222-222222222222",
                    "type": "qemu",
                }
            }
        }


class FakeSSH:
    def __init__(self, backend, listeners=None):
        self.backend = backend
        self.listeners = list(listeners or [])
        self.uuids = []

    def discover_qemu_console(self, uuid):
        self.uuids.append(uuid)
        return dict(self.backend) if self.backend else None

    def console_listener_info(self, _port):
        return list(self.listeners)


class StartAwareSSH(FakeSSH):
    def __init__(self, api):
        super().__init__(None, listeners=[])
        self.api = api

    def discover_qemu_console(self, uuid):
        self.uuids.append(uuid)
        if self.api.start_calls:
            return {
                "kind": "tcp",
                "host": "127.0.0.1",
                "port": 40001,
                "source": "qemu-process",
            }
        return None


class LiveValidationConsoleTests(unittest.TestCase):
    def test_native_endpoint_from_telnet_url(self):
        self.assertEqual(
            LiveValidator._native_endpoint_from_url("telnet://127.0.0.1:32769"),
            ("127.0.0.1", 32769),
        )

    def test_html5_guacamole_url_is_not_treated_as_telnet_port(self):
        url = (
            "/html5/#/client/MzI3NjkAYwBteXNxbA=="
            "?token=F1666351184206978A3B4C5A78E5DA6225CA557FDEDCC7199962BB1537961091"
        )
        self.assertIsNone(LiveValidator._native_endpoint_from_url(url))

    def test_console_endpoint_from_node_list_url_without_ssh(self):
        api = FakeAPI()
        validator = LiveValidator(api, ssh=None)
        node_info = api.nodes("/lab.unl")["data"]["1"]

        endpoint = validator._console_endpoint(
            "/lab.unl", 1, node_info=node_info, attempts=1, delay=0
        )

        self.assertEqual(endpoint, ("127.0.0.1", 32769))
        self.assertEqual(api.node_calls, 0)

    def test_console_endpoint_retries_until_dynamic_url_exists_without_ssh(self):
        api = DelayedAPI()
        validator = LiveValidator(api, ssh=None)

        endpoint = validator._console_endpoint("/lab.unl", 1, attempts=2, delay=0)

        self.assertEqual(endpoint, ("127.0.0.1", 32770))
        self.assertGreaterEqual(api.nodes_calls, 2)

    def test_html5_url_triggers_native_relogin_without_ssh(self):
        api = HTML5ThenNativeAPI()
        validator = LiveValidator(api, ssh=None)
        initial = api.nodes("/lab.unl")["data"]["1"]

        endpoint = validator._console_endpoint(
            "/lab.unl", 1, node_info=initial, attempts=2, delay=0
        )

        self.assertEqual(endpoint, ("127.0.0.1", 32771))
        self.assertEqual(api.login_calls, 1)

    def test_html5_session_uses_qemu_tcp_backend_when_available(self):
        api = PersistentHTML5API()
        ssh = FakeSSH(
            {
                "kind": "tcp",
                "host": "127.0.0.1",
                "port": 40001,
                "source": "qemu-process",
            }
        )
        validator = LiveValidator(api, ssh=ssh)
        initial = api.nodes("/lab.unl")["data"]["1"]

        backend = validator._console_backend(
            "/lab.unl", 1, node_info=initial, attempts=1, delay=0
        )

        self.assertEqual(backend["port"], 40001)
        self.assertEqual(ssh.uuids, ["22222222-2222-2222-2222-222222222222"])
        self.assertEqual(api.login_calls, 0)

    def test_html5_session_can_use_qemu_unix_backend(self):
        api = PersistentHTML5API()
        ssh = FakeSSH(
            {
                "kind": "unix",
                "path": "/tmp/eve-console.sock",
                "source": "qemu-process",
            }
        )
        validator = LiveValidator(api, ssh=ssh)
        initial = api.nodes("/lab.unl")["data"]["1"]

        backend = validator._console_backend(
            "/lab.unl", 1, node_info=initial, attempts=1, delay=0
        )

        self.assertEqual(backend["kind"], "unix")
        self.assertEqual(backend["path"], "/tmp/eve-console.sock")

    def test_stale_native_url_is_ignored_and_scenario_node_is_started(self):
        api = FakeAPI()
        ssh = StartAwareSSH(api)
        validator = LiveValidator(api, ssh=ssh)
        initial = api.nodes("/lab.unl")["data"]["1"]

        backend = validator._console_backend(
            "/lab.unl", 1, node_info=initial, attempts=1, delay=0
        )

        self.assertEqual(api.start_calls, 1)
        self.assertEqual(backend["source"], "qemu-process")
        self.assertEqual(backend["port"], 40001)
        self.assertNotEqual(backend["port"], 32769)


if __name__ == "__main__":
    unittest.main()
