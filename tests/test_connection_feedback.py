import unittest
from unittest.mock import patch

from ccna_lab_builder.gui.connection_feedback import _test_connection


class Entry:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class BooleanValue:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeSettings:
    def __init__(self):
        self.data = {"eve": {}}
        self.saved = False

    def save(self):
        self.saved = True


class FakeSSH:
    def __init__(self, host, username, password, port):
        self.host = host
        self.username = username
        self.password = password
        self.port = port

    def connect(self):
        return "eve-lab"


class FakeAPI:
    def __init__(self, host, username, password, https=False):
        self.host = host
        self.username = username
        self.password = password
        self.https = https

    def login(self):
        return {"status": "success"}


class FakeWindow:
    def __init__(self):
        self.host = Entry("172.16.200.156")
        self.ssh_user = Entry("root")
        self.ssh_password = Entry("secret")
        self.ssh_port = Entry("22")
        self.api_user = Entry("admin")
        self.api_password = Entry("secret")
        self.https = BooleanValue(False)
        self.settings = FakeSettings()
        self.status_updates = []
        self.logs = []
        self.ssh = None
        self.api = None

    def log(self, message):
        self.logs.append(str(message))

    def after(self, _delay, callback):
        callback()

    def _set_connection_status(self, **kwargs):
        self.status_updates.append(kwargs)


class ConnectionFeedbackTests(unittest.TestCase):
    @patch("ccna_lab_builder.gui.connection_feedback._show_connection_toast")
    @patch("ccna_lab_builder.gui.connection_feedback.EVEApi", FakeAPI)
    @patch("ccna_lab_builder.gui.connection_feedback.SSHConnection", FakeSSH)
    def test_success_uses_toast_and_updates_both_statuses(self, toast):
        window = FakeWindow()

        _test_connection(window)

        self.assertIn({"ssh": True}, window.status_updates)
        self.assertIn({"api": True}, window.status_updates)
        toast.assert_called_once_with(window, "172.16.200.156")
        self.assertTrue(window.settings.saved)
        self.assertEqual(window.settings.data["eve"]["host"], "172.16.200.156")


if __name__ == "__main__":
    unittest.main()
