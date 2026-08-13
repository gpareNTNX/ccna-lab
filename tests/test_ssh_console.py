import unittest

from ccna_lab_builder.core.ssh import SSHConnection


class QEMUConsoleParserTests(unittest.TestCase):
    def test_parses_serial_telnet_backend(self):
        command = (
            "/opt/qemu/bin/qemu-system-x86_64 -uuid abc "
            "-serial telnet:127.0.0.1:40001,server,nowait"
        )
        backend = SSHConnection.parse_qemu_console_backend(command)
        self.assertEqual(
            backend,
            {
                "kind": "tcp",
                "host": "127.0.0.1",
                "port": 40001,
                "source": "qemu-process",
            },
        )

    def test_parses_serial_unix_backend(self):
        command = (
            "/opt/qemu/bin/qemu-system-x86_64 -uuid abc "
            "-serial unix:/tmp/eve-serial.sock,server,nowait"
        )
        backend = SSHConnection.parse_qemu_console_backend(command)
        self.assertEqual(backend["kind"], "unix")
        self.assertEqual(backend["path"], "/tmp/eve-serial.sock")

    def test_parses_chardev_tcp_backend(self):
        command = (
            "/opt/qemu/bin/qemu-system-x86_64 -uuid abc "
            "-chardev socket,id=serial0,host=127.0.0.1,port=40002,server=on,wait=off "
            "-serial chardev:serial0"
        )
        backend = SSHConnection.parse_qemu_console_backend(command)
        self.assertEqual(backend["kind"], "tcp")
        self.assertEqual(backend["port"], 40002)

    def test_parses_chardev_unix_backend(self):
        command = (
            "/opt/qemu/bin/qemu-system-x86_64 -uuid abc "
            "-chardev socket,id=serial0,path=/tmp/eve.sock,server=on,wait=off "
            "-serial chardev:serial0"
        )
        backend = SSHConnection.parse_qemu_console_backend(command)
        self.assertEqual(backend["kind"], "unix")
        self.assertEqual(backend["path"], "/tmp/eve.sock")


if __name__ == "__main__":
    unittest.main()
