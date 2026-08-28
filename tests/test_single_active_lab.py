import unittest
from unittest.mock import patch

from ccna_lab_builder.gui.single_active_lab import SingleActiveLabController


class FakeApi:
    def __init__(self, fail_on=None):
        self.stopped = []
        self.fail_on = fail_on

    def stop_all(self, lab):
        self.stopped.append(lab)
        if lab == self.fail_on:
            raise RuntimeError("stop failed")
        return {"status": "success"}


class FakeWindow:
    MUTED = "muted"
    SUCCESS = "success"
    WARNING = "warning"
    ACCENT = "accent"
    DANGER = "danger"

    def __init__(self, api=None):
        self.api = api or FakeApi()
        self.ssh = object()
        self.logs = []

    def log(self, message):
        self.logs.append(str(message))

    def after(self, _delay, func):
        func()


class FakeWorkspace:
    def __init__(self, window):
        self.window = window
        self.disconnects = 0
        self.sessions = {}

    def disconnect_all(self):
        self.disconnects += 1


class SingleActiveLabTests(unittest.TestCase):
    def make_controller(self, api=None):
        window = FakeWindow(api)
        workspace = FakeWorkspace(window)
        return SingleActiveLabController(window, workspace), window, workspace

    def test_first_activation_stops_other_discovered_labs(self):
        controller, window, workspace = self.make_controller()
        with patch(
            "ccna_lab_builder.gui.single_active_lab._discover_via_ssh",
            return_value=["/labs/A.unl", "/labs/B.unl", "/labs/C.unl"],
        ):
            controller.switch_to("/labs/B.unl")

        self.assertEqual(window.api.stopped, ["/labs/A.unl", "/labs/C.unl"])
        self.assertEqual(controller.active_lab, "/labs/B.unl")
        self.assertEqual(workspace.disconnects, 1)

    def test_same_active_lab_does_not_stop_or_disconnect_again(self):
        controller, window, workspace = self.make_controller()
        with patch(
            "ccna_lab_builder.gui.single_active_lab._discover_via_ssh",
            return_value=[],
        ):
            controller.switch_to("/labs/A.unl")
            disconnects = workspace.disconnects
            controller.switch_to("/labs/A.unl")

        self.assertEqual(window.api.stopped, [])
        self.assertEqual(workspace.disconnects, disconnects)

    def test_second_switch_stops_only_tracked_active_lab(self):
        controller, window, _workspace = self.make_controller()
        with patch(
            "ccna_lab_builder.gui.single_active_lab._discover_via_ssh",
            return_value=["/labs/OLD.unl", "/labs/OTHER.unl"],
        ):
            controller.switch_to("/labs/OLD.unl")
        window.api.stopped.clear()

        with patch(
            "ccna_lab_builder.gui.single_active_lab._discover_via_ssh",
            return_value=["/labs/SHOULD-NOT-BE-SWEPT.unl"],
        ):
            controller.switch_to("/labs/NEW.unl")

        self.assertEqual(window.api.stopped, ["/labs/OLD.unl"])
        self.assertEqual(controller.active_lab, "/labs/NEW.unl")

    def test_stop_failure_aborts_target_activation(self):
        api = FakeApi(fail_on="/labs/OLD.unl")
        controller, _window, _workspace = self.make_controller(api)
        controller.active_lab = "/labs/OLD.unl"
        controller._initialized = True

        with self.assertRaises(RuntimeError):
            controller.switch_to("/labs/NEW.unl")

        self.assertEqual(controller.active_lab, "/labs/OLD.unl")

    def test_manual_stop_and_close_clears_active_lab(self):
        controller, window, workspace = self.make_controller()
        controller.active_lab = "/labs/A.unl"
        controller._initialized = True

        controller.stop_and_close_active()

        self.assertEqual(window.api.stopped, ["/labs/A.unl"])
        self.assertEqual(controller.active_lab, "")
        self.assertEqual(workspace.disconnects, 1)


if __name__ == "__main__":
    unittest.main()
