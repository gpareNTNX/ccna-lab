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

        match = re.search(r"(?:^|\s)-serial\s+unix:([^,\s]+)", command)
        if match:
            return {
                "kind": "unix",
                "path": match.group(1),
                "source": "qemu-process",
            }

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
    _PROMPT_RE = re.compile(r"(?m)^[A-Za-z0-9_.:/()\-]+[>#]\s*$")

    def __init__(self, channel):
        self.ch = channel
        self.ch.settimeout(1.0)

    @staticmethod
    def _clean_telnet(data):
        """Remove Telnet negotiation bytes while preserving IOS text."""
        out = bytearray()
        i = 0
        size = len(data)
        while i < size:
            byte = data[i]
            if byte != 255:
                out.append(byte)
                i += 1
                continue

            if i + 1 >= size:
                break

            command = data[i + 1]
            if command == 255:
                out.append(255)
                i += 2
                continue

            if command in (251, 252, 253, 254):
                i += 3
                continue

            if command == 250:
                i += 2
                while i + 1 < size:
                    if data[i] == 255 and data[i + 1] == 240:
                        i += 2
                        break
                    i += 1
                continue

            i += 2

        return out.decode(errors="replace")

    @classmethod
    def _last_prompt(cls, text):
        matches = list(cls._PROMPT_RE.finditer(str(text or "")))
        return matches[-1].group(0).strip() if matches else None

    def read(self, seconds=1.0):
        end = time.monotonic() + seconds
        parts = []
        while time.monotonic() < end:
            try:
                if self.ch.recv_ready():
                    parts.append(self.ch.recv(65535))
                    time.sleep(0.03)
                else:
                    time.sleep(0.03)
            except Exception:
                break
        return self._clean_telnet(b"".join(parts))

    def drain(self, seconds=0.15):
        """Discard stale prompt/output before issuing a new command."""
        self.read(seconds)

    def read_until_prompt(self, timeout=6.0, idle_grace=0.15):
        """Read until an IOS prompt returns instead of relying on a fixed delay."""
        deadline = time.monotonic() + timeout
        parts = []
        last_data = None
        rendered = ""

        while time.monotonic() < deadline:
            try:
                if self.ch.recv_ready():
                    parts.append(self.ch.recv(65535))
                    last_data = time.monotonic()
                    rendered = self._clean_telnet(b"".join(parts))
                else:
                    now = time.monotonic()
                    if (
                        rendered
                        and last_data is not None
                        and now - last_data >= idle_grace
                        and self._PROMPT_RE.search(rendered)
                    ):
                        break
                    time.sleep(0.03)
            except Exception:
                break

        return rendered or self._clean_telnet(b"".join(parts))

    def send(self, text):
        self.ch.send((text + "\r").encode())

    def bootstrap(self):
        self.drain()
        self.send("")
        out = self.read(1.5)
        if "initial configuration dialog" in out.lower():
            self.send("no")
            out += self.read(2.0)
        if "press return" in out.lower():
            self.send("")
            out += self.read(1.0)
        if not self._PROMPT_RE.search(out):
            self.send("")
            out += self.read_until_prompt(timeout=4.0)
        return out

    def current_prompt(self, timeout=4.0):
        """Ask IOS for its current prompt and return the final prompt string."""
        self.drain()
        self.send("")
        output = self.read_until_prompt(timeout=timeout)
        return self._last_prompt(output)

    def ensure_privileged(self, timeout=5.0):
        """Ensure the console is at privileged EXEC (hostname#) before show commands."""
        prompt = self.current_prompt(timeout=timeout)
        if not prompt:
            raise RuntimeError("Could not determine the IOS prompt before validation.")

        if "(config" in prompt.lower():
            output = self.command("end", timeout=timeout)
            prompt = self._last_prompt(output) or self.current_prompt(timeout=timeout)

        if prompt and prompt.endswith(">"):
            self.drain()
            self.send("enable")
            output = self.read(1.0)
            if "password:" in output.lower():
                raise RuntimeError(
                    "IOS enable password is required. Enter privileged EXEC manually "
                    "or remove the enable password for this training scenario."
                )
            prompt = self._last_prompt(output)
            if not prompt:
                output += self.read_until_prompt(timeout=timeout)
                prompt = self._last_prompt(output)

        if not prompt or not prompt.endswith("#") or "(config" in prompt.lower():
            raise RuntimeError(
                f"Validator could not reach privileged EXEC mode. Current prompt: {prompt or 'unknown'}"
            )
        return prompt

    def command(self, command, wait=None, timeout=None):
        """Execute a command and wait for the IOS prompt to return."""
        if timeout is None:
            timeout = max(4.0, float(wait or 0.0))
        self.drain()
        self.send(command)
        return self.read_until_prompt(timeout=timeout)

    def configure(self, commands):
        self.bootstrap()
        self.ensure_privileged()
        self.command("configure terminal")
        output = []
        for cmd in commands:
            output.append(self.command(cmd, timeout=4.0))
        output.append(self.command("end", timeout=4.0))
        output.append(self.command("write memory", timeout=8.0))
        return "\n".join(output)
