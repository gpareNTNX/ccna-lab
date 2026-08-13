import re


def _int_option(command, option):
    match = re.search(
        rf"(?:^|\s){re.escape(option)}\s+(\d+)(?=\s|$)",
        str(command or ""),
    )
    return int(match.group(1)) if match else None


def parse_qemu_wrapper_console(command):
    """Resolve the console TCP port encoded by EVE-NG qemu_wrapper arguments."""
    value = str(command or "")
    if "qemu_wrapper" not in value:
        return None

    explicit_port = _int_option(value, "-C")
    if explicit_port and 1 <= explicit_port <= 65535:
        return {
            "kind": "tcp",
            "host": "127.0.0.1",
            "port": explicit_port,
            "source": "qemu-wrapper-explicit",
        }

    pod = _int_option(value, "-T")
    device = _int_option(value, "-D")
    if pod is None or device is None:
        return None

    # EVE Community allocates a fixed block of 128 TCP ports per POD.
    # POD 0 / node 1 starts at 32769, so POD 1 / node 1 is 32897.
    port = 32768 + (pod * 128) + device
    if not 1 <= port <= 65535:
        return None

    return {
        "kind": "tcp",
        "host": "127.0.0.1",
        "port": port,
        "source": "qemu-wrapper-pod",
        "pod": pod,
        "wrapper_device": device,
    }


def install_qemu_wrapper_parser():
    """Extend SSHConnection's parser without changing its existing QEMU handling."""
    from ccna_lab_builder.core.ssh import SSHConnection

    original = SSHConnection.parse_qemu_console_backend
    if getattr(original, "_eve_wrapper_extended", False):
        return

    def extended(command):
        return original(command) or parse_qemu_wrapper_console(command)

    extended._eve_wrapper_extended = True
    SSHConnection.parse_qemu_console_backend = staticmethod(extended)
