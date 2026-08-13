import unittest

from ccna_lab_builder.core.ssh import CiscoConsole


class FakeChannel:
    def __init__(self, response_chunks):
        self.response_chunks = list(response_chunks)
        self.active = False
        self.sent = []

    def settimeout(self, _timeout):
        return None

    def send(self, data):
        self.sent.append(data)
        self.active = True
        return len(data)

    def recv_ready(self):
        return self.active and bool(self.response_chunks)

    def recv(self, _size):
        return self.response_chunks.pop(0)


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


class CiscoConsoleTests(unittest.TestCase):
    def test_command_reads_until_ios_prompt(self):
        channel = FakeChannel(
            [
                b"R1-EDGE#show ip ssh\r\n",
                b"SSH Enabled - version 2.0\r\n",
                b"Authentication timeout: 120 secs\r\n",
                b"R1-EDGE#",
            ]
        )
        console = CiscoConsole(channel)

        output = console.command("show ip ssh", timeout=1.0)

        self.assertIn("SSH Enabled - version 2.0", output)
        self.assertTrue(output.rstrip().endswith("R1-EDGE#"))

    def test_telnet_negotiation_bytes_are_removed(self):
        data = b"\xff\xfb\x01hostname R1-EDGE\r\n\xff\xfd\x03R1-EDGE#"
        output = CiscoConsole._clean_telnet(data)
        self.assertIn("hostname R1-EDGE", output)
        self.assertNotIn("\ufffd", output)

    def test_ensure_privileged_promotes_user_exec(self):
        channel = ScriptedChannel(
            [
                [b"Router>"],
                [b"Router#"],
            ]
        )
        console = CiscoConsole(channel)

        prompt = console.ensure_privileged(timeout=0.5)

        self.assertEqual(prompt, "Router#")
        self.assertIn(b"enable\r", channel.sent)

    def test_ensure_privileged_exits_config_mode(self):
        channel = ScriptedChannel(
            [
                [b"R1-EDGE(config)#"],
                [b"R1-EDGE#"],
            ]
        )
        console = CiscoConsole(channel)

        prompt = console.ensure_privileged(timeout=0.5)

        self.assertEqual(prompt, "R1-EDGE#")
        self.assertIn(b"end\r", channel.sent)


if __name__ == "__main__":
    unittest.main()
