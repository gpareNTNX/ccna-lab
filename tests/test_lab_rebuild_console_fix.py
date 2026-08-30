import unittest

from ccna_lab_builder.gui.lab_rebuild_console_fix import (
    _delete_lab_method,
    _destroy_existing_lab,
    _interactive_backend,
    _lab_exists,
)


class FakeApi:
    def __init__(self, exists=True):
        self.exists = exists
        self.calls = []

    def get_lab(self, lab):
        self.calls.append(("get_lab", lab))
        if not self.exists:
            raise RuntimeError("HTTP 404: Lab does not exist (60000).")
        return {"status": "success", "data": {"id": "lab-uuid"}}

    def stop_all(self, lab):
        self.calls.append(("stop_all", lab))
        return {"status": "success"}

    def delete_lab(self, lab):
        self.calls.append(("delete_lab", lab))
        self.exists = False
        return {"status": "success"}


class FakeController:
    def __init__(self):
        self.calls = []

    def _close_consoles(self):
        self.calls.append(("close_consoles",))

    def _stop_lab(self, lab):
        self.calls.append(("stop_lab", lab))

    def clear_if_active(self, lab):
        self.calls.append(("clear_if_active", lab))


class FakeWindow:
    def __init__(self, api, controller=None):
        self.api = api
        self._active_lab_controller = controller
        self._console_workspace = None
        self.logs = []

    def log(self, message):
        self.logs.append(str(message))


class FakeRequestApi:
    def __init__(self):
        self.calls = []

    @staticmethod
    def _path(value):
        return value.lstrip("/")

    def request(self, method, endpoint):
        self.calls.append((method, endpoint))
        return {"status": "success"}


class FakeValidator:
    def __init__(self):
        self.logs = []

    def log(self, message):
        self.logs.append(str(message))


class LabRebuildConsoleFixTests(unittest.TestCase):
    def test_delete_lab_uses_documented_delete_endpoint(self):
        api = FakeRequestApi()
        result = _delete_lab_method(api, "/CCNA/Test Lab.unl")
        self.assertEqual(result["status"], "success")
        self.assertEqual(api.calls, [("DELETE", "/labs/CCNA/Test Lab.unl")])

    def test_lab_exists_returns_false_for_eve_missing_lab_error(self):
        self.assertFalse(_lab_exists(FakeApi(exists=False), "/missing.unl"))

    def test_destroy_existing_lab_closes_stops_deletes_and_clears(self):
        api = FakeApi(exists=True)
        controller = FakeController()
        window = FakeWindow(api, controller)

        changed = _destroy_existing_lab(window, "/CCNA/lab.unl")

        self.assertTrue(changed)
        self.assertIn(("close_consoles",), controller.calls)
        self.assertIn(("stop_lab", "/CCNA/lab.unl"), controller.calls)
        self.assertIn(("clear_if_active", "/CCNA/lab.unl"), controller.calls)
        self.assertIn(("delete_lab", "/CCNA/lab.unl"), api.calls)
        self.assertFalse(api.exists)

    def test_destroy_missing_lab_is_noop(self):
        api = FakeApi(exists=False)
        controller = FakeController()
        window = FakeWindow(api, controller)

        self.assertFalse(_destroy_existing_lab(window, "/CCNA/missing.unl"))
        self.assertEqual(controller.calls, [])

    def test_interactive_console_uses_normal_backend_first(self):
        calls = []
        validator = FakeValidator()

        def base(_validator, _lab, _node, **_kwargs):
            calls.append("base")
            return {"kind": "tcp", "port": 40001}

        def recovered(_validator, _lab, _node, **_kwargs):
            calls.append("recovered")
            return {"kind": "tcp", "port": 40002}

        backend = _interactive_backend(
            base, recovered, validator, "/lab.unl", 1, {}, 15, 1.0
        )
        self.assertEqual(backend["port"], 40001)
        self.assertEqual(calls, ["base"])

    def test_interactive_console_recovers_only_after_normal_lookup_fails(self):
        calls = []
        validator = FakeValidator()

        def base(_validator, _lab, _node, **_kwargs):
            calls.append("base")
            raise RuntimeError("No exact console backend available for node 1")

        def recovered(_validator, _lab, _node, **_kwargs):
            calls.append("recovered")
            return {"kind": "tcp", "port": 40002}

        backend = _interactive_backend(
            base, recovered, validator, "/lab.unl", 1, {}, 15, 1.0
        )
        self.assertEqual(backend["port"], 40002)
        self.assertEqual(calls, ["base", "recovered"])
        self.assertTrue(any("controlled recovery" in line for line in validator.logs))


if __name__ == "__main__":
    unittest.main()
