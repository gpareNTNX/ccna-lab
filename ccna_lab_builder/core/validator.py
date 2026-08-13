import re
from dataclasses import dataclass, field


_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_PROMPT_RE = re.compile(r"^[A-Za-z0-9_.:/()\-]+[>#]\s*$")


@dataclass
class CheckResult:
    node: str
    command: str
    passed: bool
    missing: list
    output: str
    expected: list = field(default_factory=list)
    matched: list = field(default_factory=list)
    remediation: list = field(default_factory=list)


class Validator:
    @staticmethod
    def _apply_backspaces(text):
        chars = []
        for char in text:
            if char == "\b":
                if chars:
                    chars.pop()
            else:
                chars.append(char)
        return "".join(chars)

    @classmethod
    def clean_output(cls, command, output):
        """Normalize IOS console output and remove command echo/prompt lines."""
        text = str(output or "").replace("\x00", "")
        text = _ANSI_RE.sub("", text)
        text = cls._apply_backspaces(text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        command_norm = re.sub(r"\s+", " ", str(command).strip()).casefold()
        cleaned = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            compact = re.sub(r"\s+", " ", line)
            compact_cf = compact.casefold()

            # Remove a plain command echo or an IOS prompt followed by the echo.
            if compact_cf == command_norm:
                continue
            if compact_cf.endswith("#" + command_norm) or compact_cf.endswith(">" + command_norm):
                continue

            # Remove a prompt-only line such as R1-EDGE# or SW1(config)#.
            if _PROMPT_RE.fullmatch(compact):
                continue

            cleaned.append(compact)

        return "\n".join(cleaned)

    @staticmethod
    def _normalized_search_text(value):
        return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

    @classmethod
    def _suggest_remediation(cls, check, missing):
        if not missing:
            return []

        command = cls._normalized_search_text(check.get("command", ""))
        expected = [str(x) for x in check.get("contains", [])]

        if "running-config | include hostname" in command:
            hostname_line = next(
                (item for item in expected if item.lower().startswith("hostname ")),
                "hostname <EXPECTED-HOSTNAME>",
            )
            return [
                "configure terminal",
                hostname_line,
                "end",
                "write memory",
            ]

        if command == "show ip ssh":
            return [
                "configure terminal",
                "ip domain-name ccna.lab",
                "username admin privilege 15 secret <PASSWORD>",
                "crypto key generate rsa modulus 2048",
                "ip ssh version 2",
                "line vty 0 4",
                "login local",
                "transport input ssh",
                "end",
                "write memory",
            ]

        if command == "show vlan brief":
            commands = ["configure terminal"]
            index = 0
            while index < len(expected):
                if expected[index].isdigit():
                    vlan = expected[index]
                    commands.append(f"vlan {vlan}")
                    if index + 1 < len(expected) and not expected[index + 1].isdigit():
                        commands.append(f"name {expected[index + 1]}")
                        index += 1
                index += 1
            commands.extend(["end", "write memory"])
            return commands

        if command == "show interfaces trunk":
            interface = next((x for x in expected if re.match(r"^[A-Za-z]+\d+/\d+$", x)), "<INTERFACE>")
            native = next((x for x in expected if x.isdigit()), "99")
            return [
                "configure terminal",
                f"interface {interface}",
                "switchport mode trunk",
                f"switchport trunk native vlan {native}",
                "switchport trunk allowed vlan 10,20,30,40,99",
                "no shutdown",
                "end",
                "write memory",
            ]

        if command == "show etherchannel summary":
            return [
                "configure terminal",
                "interface range <LINK-1>,<LINK-2>",
                "channel-group 1 mode active",
                "no shutdown",
                "interface port-channel 1",
                "switchport mode trunk",
                "end",
                "write memory",
            ]

        if command == "show spanning-tree root":
            vlans = [re.sub(r"(?i)^vl", "", item) for item in expected if re.match(r"(?i)^vl\d+$", item)]
            vlan_text = ",".join(vlans) if vlans else "<VLANS>"
            return [
                "configure terminal",
                "spanning-tree mode rapid-pvst",
                f"spanning-tree vlan {vlan_text} root primary",
                "end",
                "write memory",
            ]

        if command == "show ip dhcp pool":
            pool = expected[0] if expected else "USERS"
            network = next((x for x in expected if re.match(r"^\d+\.\d+\.\d+\.\d+$", x)), "10.10.10.0")
            return [
                "configure terminal",
                f"ip dhcp pool {pool}",
                f"network {network} 255.255.255.0",
                "default-router 10.10.10.1",
                "end",
                "write memory",
            ]

        if "running-config | include ip nat" in command:
            return [
                "configure terminal",
                "interface <INSIDE-INTERFACE>",
                "ip nat inside",
                "exit",
                "interface <OUTSIDE-INTERFACE>",
                "ip nat outside",
                "exit",
                "access-list 1 permit <INSIDE-SUBNET> <WILDCARD>",
                "ip nat inside source list 1 interface <OUTSIDE-INTERFACE> overload",
                "end",
                "write memory",
            ]

        if command == "show access-lists":
            return [
                "configure terminal",
                "ip access-list extended <ACL-NAME>",
                "<PERMIT/DENY RULES>",
                "exit",
                "interface <INTERFACE>",
                "ip access-group <ACL-NAME> <in|out>",
                "end",
                "write memory",
            ]

        if command.startswith("show port-security interface"):
            interface = check.get("command", "").split()[-1]
            return [
                "configure terminal",
                f"interface {interface}",
                "switchport mode access",
                "switchport port-security",
                "switchport port-security maximum 2",
                "switchport port-security mac-address sticky",
                "switchport port-security violation restrict",
                "end",
                "write memory",
            ]

        if command == "show ip dhcp snooping":
            return [
                "configure terminal",
                "ip dhcp snooping",
                "ip dhcp snooping vlan 10",
                "interface <UPLINK>",
                "ip dhcp snooping trust",
                "end",
                "write memory",
            ]

        if command == "show ip arp inspection":
            return [
                "configure terminal",
                "ip arp inspection vlan 10",
                "interface <UPLINK>",
                "ip arp inspection trust",
                "end",
                "write memory",
            ]

        if command == "show ip ospf neighbor":
            return [
                "configure terminal",
                "router ospf 10",
                "router-id <ROUTER-ID>",
                "network <NETWORK> <WILDCARD> area 0",
                "end",
                "write memory",
            ]

        if "show ip interface brief" in command:
            ip_value = next((x for x in missing if re.match(r"^\d+\.\d+\.\d+\.\d+$", x)), "<EXPECTED-IP>")
            return [
                "configure terminal",
                "interface <EXPECTED-INTERFACE>",
                f"ip address {ip_value} <SUBNET-MASK>",
                "no shutdown",
                "end",
                "write memory",
            ]

        if "show ipv6 interface brief" in command:
            ip_value = next((x for x in missing if ":" in x), "<EXPECTED-IPV6>")
            return [
                "configure terminal",
                "ipv6 unicast-routing",
                "interface <EXPECTED-INTERFACE>",
                f"ipv6 address {ip_value}/64",
                "no shutdown",
                "end",
                "write memory",
            ]

        return []

    @classmethod
    def validate_output(cls, check, output):
        cleaned = cls.clean_output(check.get("command", ""), output)
        searchable = cls._normalized_search_text(cleaned)
        expected = [str(token) for token in check.get("contains", [])]

        matched = []
        missing = []
        for token in expected:
            normalized_token = cls._normalized_search_text(token)
            if normalized_token and normalized_token in searchable:
                matched.append(token)
            else:
                missing.append(token)

        return CheckResult(
            node=check["node"],
            command=check["command"],
            passed=not missing,
            missing=missing,
            output=cleaned,
            expected=expected,
            matched=matched,
            remediation=cls._suggest_remediation(check, missing),
        )

    def validate_pasted(self, scenario, outputs):
        results = []
        for check in scenario.get("checks", []):
            key = (check["node"], check["command"])
            results.append(self.validate_output(check, outputs.get(key, "")))
        return results

    @staticmethod
    def score(results):
        if not results:
            return 0
        return round(100 * sum(1 for result in results if result.passed) / len(results))
