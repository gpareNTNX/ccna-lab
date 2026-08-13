import unittest

from ccna_lab_builder.core.console_auth import (
    LAB_ENABLE_SECRET,
    LAB_IOS_PASSWORD,
    LAB_IOS_USERNAME,
)
from ccna_lab_builder.core.ssh import CiscoConsole


class ScriptedChannel:
    def __init__(self, responses_per_send):
        self.responses_per_send = [list(chunks) for chunks in responses_per_send]
        self.current = []
        self.sent = []

    def settimeout(self, _timeout):
        return None

    def send(self, data):
        self.sent.append(data)
        self.current = self.responses_per_send.pop(0) if self.responses_per_send else []
        return len(data)

    def recv_ready(self):
        return bool(self.current)

    def recv(self, _size):
        return self.current.pop(0)


class ConsoleAuthenticationTests(unittest.TestCase):
    def test_wait_for_prompt_logs_in_with_training_credentials(self):
        channel = ScriptedChannel(
            [
                [b"Username: "],
                [b"Password: "],
                [b"R1-EDGE>"],
            ]
        )
        console = CiscoConsole(channel)

        prompt = console.wait_for_prompt(timeout=1.0, pulse=0.05)

        self.assertEqual(prompt, "R1-EDGE>")
        self.assertIn((LAB_IOS_USERNAME + "\r").encode(), channel.sent)
        self.assertIn((LAB_IOS_PASSWORD + "\r").encode(), channel.sent)

    def test_ensure_privileged_uses_training_enable_secret(self):
        channel = ScriptedChannel(
            [
                [b"R1-EDGE>"],
                [b"Password: "],
                [b"R1-EDGE#"],
            ]
        )
        console = CiscoConsole(channel)

        prompt = console.ensure_privileged(timeout=0.5)

        self.assertEqual(prompt, "R1-EDGE#")
        self.assertIn(b"enable\r", channel.sent)
        self.assertIn((LAB_ENABLE_SECRET + "\r").encode(), channel.sent)


if __name__ == "__main__":
    unittest.main()
