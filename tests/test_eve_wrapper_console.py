import unittest

from ccna_lab_builder.core.eve_wrapper_console import parse_qemu_wrapper_console
from ccna_lab_builder.core.ssh import SSHConnection


class EveWrapperConsoleTests(unittest.TestCase):
    def test_community_pod_one_node_one_maps_to_32897(self):
        command = (
            "/opt/unetlab/wrappers/qemu_wrapper -T 1 -D 1 -t R1-EDGE "
            "-F /opt/qemu-2.4.0/bin/qemu-system-x86_64 -d 0 -- -nographic"
        )

        backend = parse_qemu_wrapper_console(command)

        self.assertEqual(backend["host"], "127.0.0.1")
        self.assertEqual(backend["port"], 32897)
        self.assertEqual(backend["pod"], 1)
        self.assertEqual(backend["wrapper_device"], 1)

    def test_explicit_dynamic_console_port_wins(self):
        command = (
            "/opt/unetlab/wrappers/qemu_wrapper -C 54311 -T 2 -D 1 "
            "-F /opt/qemu/bin/qemu-system-x86_64 -- -nographic"
        )

        backend = parse_qemu_wrapper_console(command)

        self.assertEqual(backend["port"], 54311)
        self.assertEqual(backend["source"], "qemu-wrapper-explicit")

    def test_ssh_parser_is_extended_for_wrapper_stdio_console(self):
        command = (
            "/opt/unetlab/wrappers/qemu_wrapper -T 1 -D 1 -t R1-EDGE "
            "-F /opt/qemu-2.4.0/bin/qemu-system-x86_64 -d 0 -- -nographic"
        )

        backend = SSHConnection.parse_qemu_console_backend(command)

        self.assertEqual(backend["port"], 32897)

    def test_plain_qemu_without_console_remains_unresolved(self):
        self.assertIsNone(
            parse_qemu_wrapper_console(
                "/opt/qemu/bin/qemu-system-x86_64 -nographic -m 1024"
            )
        )


if __name__ == "__main__":
    unittest.main()
