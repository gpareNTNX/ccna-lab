import unittest

from ccna_lab_builder.gui.runtime_recovery import (
    _force_node_recycle,
    _recover_stuck_lab_runtimes,
    _signal_lab_runtimes,
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


class RecoveryAPI:
    def __init__(self):
        self.stop_node_calls = []

    def nodes(self, _lab):
        return {"data": {"1": {"status": 2}, "2": {"status": 2}}}

    def stop_node(self, lab, node_id):
        self.stop_node_calls.append((lab, str(node_id)))
        return {"status": "success"}


class RecoverySSH:
    def __init__(self, stop_on_term=True):
        self.commands = []
        self.terminated = False
        self.killed = False
        self.stop_on_term = stop_on_term

    def exec(self, command):
        self.commands.append(command)
        if "sig=TERM" in command:
            if self.stop_on_term:
                self.terminated = True
            return "1234\n", ""
        if "sig=KILL" in command:
            self.killed = True
            self.terminated = True
            return "1234\n", ""
        if self.terminated:
            return "", ""
        return "1234\n", ""


class RecoveryWindow:
    def __init__(self, stop_on_term=True):
        self.api = RecoveryAPI()
        self.ssh = RecoverySSH(stop_on_term=stop_on_term)
        self.logs = []

    def log(self, message):
        self.logs.append(message)


class RecoveryController:
    def __init__(self, stop_on_term=True):
        self.window = RecoveryWindow(stop_on_term=stop_on_term)


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

    def test_scoped_signal_targets_only_exact_lab_uuid(self):
        controller = RecoveryController()

        signaled = _signal_lab_runtimes(controller, "lab-uuid", "TERM")

        self.assertEqual(signaled, ["1234"])
        command = controller.window.ssh.commands[-1]
        self.assertIn("/lab-uuid/", command)
        self.assertIn("/opt/unetlab/tmp/", command)
        self.assertIn("kill -s", command)
        self.assertNotIn("killall", command)
        self.assertNotIn("pkill", command)

    def test_stuck_lab_escalates_to_per_node_stop_then_scoped_sigterm(self):
        controller = RecoveryController(stop_on_term=True)

        recovered = _recover_stuck_lab_runtimes(
            controller,
            "/CCNA-200-301/CCNA-07-STP-RSTP.unl",
            "lab-uuid",
            graceful_timeout=0,
            node_timeout=0,
            term_timeout=0,
            kill_timeout=0,
            poll=0,
        )

        self.assertTrue(recovered)
        self.assertEqual(
            controller.window.api.stop_node_calls,
            [
                ("/CCNA-200-301/CCNA-07-STP-RSTP.unl", "1"),
                ("/CCNA-200-301/CCNA-07-STP-RSTP.unl", "2"),
            ],
        )
        self.assertTrue(any("sig=TERM" in cmd for cmd in controller.window.ssh.commands))
        self.assertFalse(any("sig=KILL" in cmd for cmd in controller.window.ssh.commands))

    def test_sigkill_is_last_resort_and_still_lab_scoped(self):
        controller = RecoveryController(stop_on_term=False)

        recovered = _recover_stuck_lab_runtimes(
            controller,
            "/lab.unl",
            "lab-uuid",
            graceful_timeout=0,
            node_timeout=0,
            term_timeout=0,
            kill_timeout=0,
            poll=0,
        )

        self.assertTrue(recovered)
        kill_commands = [cmd for cmd in controller.window.ssh.commands if "sig=KILL" in cmd]
        self.assertEqual(len(kill_commands), 1)
        self.assertIn("/lab-uuid/", kill_commands[0])
        self.assertNotIn("killall", kill_commands[0])
        self.assertNotIn("pkill", kill_commands[0])


if __name__ == "__main__":
    unittest.main()
