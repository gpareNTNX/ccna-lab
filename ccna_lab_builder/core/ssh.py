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
