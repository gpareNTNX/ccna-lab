import unittest

from ccna_lab_builder.core.live_validation import LiveValidator


class FakeAPI:
    def __init__(self):
        self.nodes_calls = 0
        self.node_calls = 0
        self.login_calls = 0

    def login(self):
        self.login_calls += 1
        return {"status": "success"}

    def nodes(self, _lab):
        self.nodes_calls += 1
        return {
            "data": {
                "1": {
                    "name": "R1-EDGE",
                    "console": "telnet",
                    "url": "telnet://127.0.0.1:32769",
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
                }
            }
        }


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

    def test_console_endpoint_from_node_list_url(self):
        api = FakeAPI()
        validator = LiveValidator(api, ssh=None)
        node_info = api.nodes("/lab.unl")["data"]["1"]

        endpoint = validator._console_endpoint(
            "/lab.unl", 1, node_info=node_info, attempts=1, delay=0
        )

        self.assertEqual(endpoint, ("127.0.0.1", 32769))
        self.assertEqual(api.node_calls, 0)

    def test_console_endpoint_retries_until_dynamic_url_exists(self):
        api = DelayedAPI()
        validator = LiveValidator(api, ssh=None)

        endpoint = validator._console_endpoint("/lab.unl", 1, attempts=2, delay=0)

        self.assertEqual(endpoint, ("127.0.0.1", 32770))
        self.assertGreaterEqual(api.nodes_calls, 2)

    def test_html5_url_triggers_native_relogin(self):
        api = HTML5ThenNativeAPI()
        validator = LiveValidator(api, ssh=None)
        initial = api.nodes("/lab.unl")["data"]["1"]

        endpoint = validator._console_endpoint(
            "/lab.unl", 1, node_info=initial, attempts=2, delay=0
        )

        self.assertEqual(endpoint, ("127.0.0.1", 32771))
        self.assertEqual(api.login_calls, 1)


if __name__ == "__main__":
    unittest.main()
