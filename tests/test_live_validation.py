import unittest

from ccna_lab_builder.core.live_validation import LiveValidator


class FakeAPI:
    def __init__(self):
        self.nodes_calls = 0
        self.node_calls = 0

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


class DelayedAPI:
    def __init__(self):
        self.nodes_calls = 0

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

    def node(self, _lab, _node_id):
        return {"data": {}}


class LiveValidationConsoleTests(unittest.TestCase):
    def test_console_port_from_node_list_url(self):
        api = FakeAPI()
        validator = LiveValidator(api, ssh=None)
        node_info = api.nodes("/lab.unl")["data"]["1"]

        port = validator._console_port(
            "/lab.unl", 1, node_info=node_info, attempts=1, delay=0
        )

        self.assertEqual(port, 32769)
        self.assertEqual(api.node_calls, 0)

    def test_console_port_retries_until_dynamic_url_exists(self):
        api = DelayedAPI()
        validator = LiveValidator(api, ssh=None)

        port = validator._console_port("/lab.unl", 1, attempts=2, delay=0)

        self.assertEqual(port, 32770)
        self.assertGreaterEqual(api.nodes_calls, 2)


if __name__ == "__main__":
    unittest.main()
