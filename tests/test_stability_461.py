import unittest

from ccna_lab_builder.gui.stability_461 import _close_lab_method, _console_layers


class FakeRequestApi:
    def __init__(self):
        self.calls = []

    def request(self, method, endpoint):
        self.calls.append((method, endpoint))
        return {"status": "success"}


class Stability461Tests(unittest.TestCase):
    def test_close_lab_uses_eve_close_endpoint(self):
        api = FakeRequestApi()
        result = _close_lab_method(api)
        self.assertEqual(result["status"], "success")
        self.assertEqual(api.calls, [("DELETE", "/labs/close")])

    def test_plain_console_backend_remains_the_stable_base(self):
        def backend(_self, _lab, _node, **_kwargs):
            return {"kind": "tcp", "port": 32769}

        base, recovered = _console_layers(backend)
        self.assertIs(base, backend)
        self.assertIs(recovered, backend)


if __name__ == "__main__":
    unittest.main()
