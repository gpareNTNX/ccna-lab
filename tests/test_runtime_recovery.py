import unittest

from ccna_lab_builder.gui.runtime_recovery import (
    _force_node_recycle,
    _wait_for_lab_runtimes_to_stop,
)


class FakeAPI:
    def __init__(self):
        self.status = 2
        self.stop_calls = 0
        self.start_calls = 0

    def node(self, _lab, _node_id):
        return {"data": {"status": self.status, "uuid": "node-uuid"}}

    def nodes(self, _lab):
        return {"data": {"1": {"status": self.status, "uuid": "node-uuid"}}}

    def stop_node(self, _lab, _node_id):
        self.stop_calls += 1
        self.status = 0
        return {"status": "success"}

    def start_node(self, _lab, _node_id):
        self.start_calls += 1
        self.status = 2
        return {"status": "success"}


class FakeValidator:
    def __init__(self):
        self.api = FakeAPI()
        self.ssh = object()
        self.logs = []

    def log(self, message):
        self.logs.append(message)

    def _runtime_backend(self, _node_id):
        if self.api.start_calls:
            return {
                "kind": "tcp",
                "host": "127.0.0.1",
                "port": 32769,
                "source": "eve-runtime",
            }
        return None

    def _qemu_backend(self, _node_info):
        return None


class FakeSSH:
    def __init__(self):
        self.calls = 0

    def exec(self, _command):
        self.calls += 1
        if self.calls == 1:
            return "1234\n", ""
        return "", ""


class FakeWindow:
    def __init__(self):
        self.ssh = FakeSSH()
        self.logs = []

    def log(self, message):
        self.logs.append(message)


class FakeController:
    def __init__(self):
        self.window = FakeWindow()


class RuntimeRecoveryTests(unittest.TestCase):
    def test_stale_running_node_is_stopped_and_restarted(self):
        validator = FakeValidator()

        backend, candidate = _force_node_recycle(
            validator,
            "/lab.unl",
            1,
            {"status": 2, "uuid": "node-uuid"},
            stop_wait=0,
            start_wait=0,
            poll=0,
        )

        self.assertEqual(validator.api.stop_calls, 1)
        self.assertEqual(validator.api.start_calls, 1)
        self.assertEqual(candidate["status"], 2)
        self.assertEqual(backend["source"], "eve-runtime")

    def test_lab_stop_waits_until_runtime_process_disappears(self):
        controller = FakeController()

        stopped = _wait_for_lab_runtimes_to_stop(
            controller,
            "/lab.unl",
            "lab-uuid",
            timeout=0.2,
            poll=0.01,
        )

        self.assertTrue(stopped)
        self.assertGreaterEqual(controller.window.ssh.calls, 2)
        self.assertTrue(
            any("Confirmed all QEMU runtimes stopped" in line for line in controller.window.logs)
        )


if __name__ == "__main__":
    unittest.main()
