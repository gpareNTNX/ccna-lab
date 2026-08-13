import re
import shlex
import time

import paramiko
from scp import SCPClient


class SSHConnection:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = int(port)
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=12,
            look_for_keys=False,
            allow_agent=False,
        )
        return self.exec("hostname")[0].strip()

    def close(self):
        if self.client:
            self.client.close()
            self.client = None

    def exec(self, command):
        if not self.client:
            raise RuntimeError("SSH is not connected.")
        _, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(errors="replace"), stderr.read().decode(errors="replace")

    def upload(self, local_path, remote_path):
        if not self.client:
            raise RuntimeError("SSH is not connected.")
        with SCPClient(self.client.get_transport()) as scp:
            scp.put(str(local_path), remote_path)

    def installed_qemu_images(self):
        out, _ = self.exec(
            r"find /opt/unetlab/addons/qemu -mindepth 1 -maxdepth 1 -type d "
            r"-printf '%f\n' 2>/dev/null | sort"
        )
        return [x.strip() for x in out.splitlines() if x.strip()]

    def console_listener_info(self, port):
        """Return listening TCP sockets on the EVE host for a console port."""
        port = int(port)
        out, _ = self.exec(
            f"ss -ltnH 2>/dev/null | awk '$4 ~ /:{port}$/ {{print $4}}'"
        )
        return [line.strip() for line in out.splitlines() if line.strip()]

    @staticmethod
    def parse_qemu_console_backend(command):
        """Extract a QEMU serial-console backend from a running command line."""
        if not command:
            return None

        # Common EVE/QEMU form: -serial telnet:127.0.0.1:32769,server,nowait
        match = re.search(
            r"(?:^|\s)-serial\s+(?:telnet|tcp):([^,:\s]+):(\d+)(?:[,\s]|$)",
            command,
        )
        if match:
            return {
                "kind": "tcp",
                "host": match.group(1),
                "port": int(match.group(2)),
                "source": "qemu-process",
            }

        # Direct UNIX serial socket.
        match = re.search(r"(?:^|\s)-serial\s+unix:([^,\s]+)", command)
        if match:
            return {
                "kind": "unix",
                "path": match.group(1),
                "source": "qemu-process",
            }

        # Modern QEMU can define a socket chardev and attach serial to it.
        serial_ref = re.search(r"(?:^|\s)-serial\s+chardev:([^\s]+)", command)
        serial_id = serial_ref.group(1) if serial_ref else None
        for match in re.finditer(r"(?:^|\s)-chardev\s+socket,([^\s]+)", command):
            options = match.group(1)
            values = {}
            for item in options.split(","):
                if "=" in item:
                    key, value = item.split("=", 1)
                    values[key] = value
            if serial_id and values.get("id") != serial_id:
                continue
            if values.get("host") and values.get("port", "").isdigit():
                return {
                    "kind": "tcp",
                    "host": values["host"],
                    "port": int(values["port"]),
                    "source": "qemu-process",
                }
            if values.get("path"):
                return {
                    "kind": "unix",
                    "path": values["path"],
                    "source": "qemu-process",
                }

        return None

    def discover_qemu_console(self, uuid):
        """Find the real serial backend from the running QEMU process UUID."""
        if not uuid:
            return None
        command = (
            "ps -eo args= | grep -F -- "
            + shlex.quote(str(uuid))
            + " | grep -E '[q]emu-system|[q]emu-kvm' | head -n 1"
        )
        out, _ = self.exec(command)
        qemu_command = out.strip()
        backend = self.parse_qemu_console_backend(qemu_command)
        if backend:
            backend["uuid"] = str(uuid)
        return backend

    def open_eve_console(self, port, target_host="127.0.0.1"):
        if not self.client:
            raise RuntimeError("SSH is not connected.")

        port = int(port)
        transport = self.client.get_transport()
        if transport is None or not transport.is_active():
            raise RuntimeError("SSH transport is not active.")

        targets = []
        for host in (target_host, "127.0.0.1", self.host):
            if host and host not in targets:
                targets.append(host)

        last_error = None
        for host in targets:
            try:
                return transport.open_channel(
                    "direct-tcpip",
                    (host, port),
                    ("127.0.0.1", 0),
                )
            except paramiko.ssh_exception.ChannelException as exc:
                last_error = exc

        listeners = self.console_listener_info(port)
        listener_text = ", ".join(listeners) if listeners else "none"
        raise RuntimeError(
            f"EVE console TCP connection failed for port {port}. "
            f"Tried targets: {', '.join(targets)}. "
            f"Listening sockets reported by EVE-NG: {listener_text}. "
            f"SSH channel error: {last_error}"
        ) from last_error

    def open_unix_console(self, path):
        """Bridge a remote UNIX serial socket over an SSH session channel."""
        if not self.client:
            raise RuntimeError("SSH is not connected.")
        transport = self.client.get_transport()
        if transport is None or not transport.is_active():
            raise RuntimeError("SSH transport is not active.")

        tool, _ = self.exec("command -v socat || command -v nc || true")
        tool = tool.strip().splitlines()[0] if tool.strip() else ""
        if not tool:
            raise RuntimeError(
                "QEMU uses a UNIX console socket, but neither socat nor nc is available on EVE-NG."
            )

        channel = transport.open_session()
        channel.set_combine_stderr(True)
        if tool.endswith("socat"):
            command = "exec socat - " + shlex.quote("UNIX-CONNECT:" + path)
        else:
            command = "exec nc -U " + shlex.quote(path)
        channel.exec_command(command)
        return channel

    def open_console_backend(self, backend):
        kind = backend.get("kind") if isinstance(backend, dict) else None
        if kind == "tcp":
            return self.open_eve_console(
                backend["port"], target_host=backend.get("host", "127.0.0.1")
            )
        if kind == "unix":
            return self.open_unix_console(backend["path"])
        raise RuntimeError(f"Unsupported EVE console backend: {backend}")


class CiscoConsole:
    def __init__(self, channel):
        self.ch = channel
        self.ch.settimeout(1.0)

    @staticmethod
    def _clean_telnet(data):
        out = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 255:
                if i + 2 < len(data):
                    i += 3
                else:
                    break
            else:
                out.append(data[i])
                i += 1
        return out.decode(errors="replace")

    def read(self, seconds=1.0):
        end = time.time() + seconds
        parts = []
        while time.time() < end:
            try:
                if self.ch.recv_ready():
                    parts.append(self.ch.recv(65535))
                    time.sleep(0.05)
                else:
                    time.sleep(0.05)
            except Exception:
                break
        return self._clean_telnet(b"".join(parts))

    def send(self, text):
        self.ch.send((text + "\r").encode())

    def bootstrap(self):
        self.send("")
        out = self.read(1.5)
        if "initial configuration dialog" in out.lower():
            self.send("no")
            out += self.read(2)
        if "press return" in out.lower():
            self.send("")
            out += self.read(1)
        return out

    def command(self, command, wait=1.2):
        self.send(command)
        return self.read(wait)

    def configure(self, commands):
        self.bootstrap()
        self.command("enable")
        self.command("configure terminal")
        output = []
        for cmd in commands:
            output.append(self.command(cmd, 0.25))
        output.append(self.command("end"))
        output.append(self.command("write memory", 1.5))
        return "\n".join(output)
