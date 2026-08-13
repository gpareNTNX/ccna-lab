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
            if compact_cf == command_norm:
                continue
            if compact_cf.endswith("#" + command_norm) or compact_cf.endswith(">" + command_norm):
                continue
            if _PROMPT_RE.fullmatch(compact):
                continue
            cleaned.append(compact)
        return "\n".join(cleaned)

    @staticmethod
    def _normalized_search_text(value):
        return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

    @staticmethod
    def _assertion_label(assertion):
        if assertion.get("label"):
            return str(assertion["label"])
        kind = assertion.get("type", "contains")
        if kind in {"contains", "not_contains"}:
            return f"{kind}: {assertion.get('value', '')}"
        if kind == "regex":
            return f"regex: {assertion.get('pattern', '')}"
        if kind == "interface_ipv4":
            return f"{assertion.get('interface')}={assertion.get('ip')}"
        if kind == "vlan":
            return f"VLAN {assertion.get('id')} {assertion.get('name', '')}".strip()
        if kind == "ospf_neighbor":
            return f"OSPF neighbor {assertion.get('router_id')} {assertion.get('state', 'FULL')}"
        if kind == "route":
            return f"route {assertion.get('prefix')} {assertion.get('code', '')}".strip()
        if kind == "trunk":
            return f"trunk {assertion.get('interface')} native {assertion.get('native_vlan', 'any')}"
        if kind == "etherchannel":
            return f"EtherChannel {assertion.get('port_channel', 'Po1')}"
        if kind == "hsrp":
            return f"HSRP {assertion.get('interface', '')} {assertion.get('state', 'Active')}".strip()
        if kind == "cdp_neighbor":
            return f"CDP neighbor {assertion.get('device_id')}"
        if kind == "ssh_enabled":
            return "SSH Enabled"
        return str(kind)

    @classmethod
    def _evaluate_assertion(cls, assertion, cleaned):
        kind = assertion.get("type", "contains")
        searchable = cls._normalized_search_text(cleaned)
        lines = cleaned.splitlines()

        if kind == "contains":
            value = cls._normalized_search_text(assertion.get("value", ""))
            return bool(value) and value in searchable
        if kind == "not_contains":
            value = cls._normalized_search_text(assertion.get("value", ""))
            return bool(value) and value not in searchable
        if kind == "regex":
            pattern = str(assertion.get("pattern", ""))
            return bool(pattern) and re.search(
                pattern, cleaned, re.IGNORECASE | re.MULTILINE
            ) is not None
        if kind == "ssh_enabled":
            return re.search(r"\bSSH\s+Enabled\b", cleaned, re.IGNORECASE) is not None

        if kind == "interface_ipv4":
            interface = str(assertion.get("interface", "")).casefold()
            ip = str(assertion.get("ip", ""))
            wanted_status = str(assertion.get("status", "")).casefold()
            wanted_protocol = str(assertion.get("protocol", "")).casefold()
            for line in lines:
                tokens = line.split()
                if len(tokens) < 6 or tokens[0].casefold() != interface or tokens[1] != ip:
                    continue
                protocol = tokens[-1].casefold()
                status = " ".join(tokens[4:-1]).casefold()
                if wanted_status and status != wanted_status:
                    continue
                if wanted_protocol and protocol != wanted_protocol:
                    continue
                return True
            return False

        if kind == "vlan":
            vlan_id = str(assertion.get("id", ""))
            name = str(assertion.get("name", "")).casefold()
            for line in lines:
                tokens = line.split()
                if not tokens or tokens[0] != vlan_id:
                    continue
                if name and (len(tokens) < 2 or tokens[1].casefold() != name):
                    continue
                return True
            return False

        if kind == "ospf_neighbor":
            router_id = str(assertion.get("router_id", ""))
            state = str(assertion.get("state", "FULL")).upper()
            return any(line.startswith(router_id) and state in line.upper() for line in lines)

        if kind == "route":
            prefix = str(assertion.get("prefix", ""))
            code = str(assertion.get("code", "")).upper()
            via = str(assertion.get("via", ""))
            for line in lines:
                if prefix not in line:
                    continue
                if code and not line.upper().startswith(code):
                    continue
                if via and via not in line:
                    continue
                return True
            return False

        if kind == "trunk":
            interface = str(assertion.get("interface", "")).casefold()
            native_vlan = str(assertion.get("native_vlan", ""))
            for line in lines:
                tokens = line.split()
                if not tokens or tokens[0].casefold() != interface:
                    continue
                if native_vlan and native_vlan not in tokens:
                    continue
                if "trunk" not in line.casefold() and "on" not in tokens:
                    continue
                return True
            return False

        if kind == "etherchannel":
            port_channel = str(assertion.get("port_channel", "Po1")).casefold()
            protocol = str(assertion.get("protocol", "")).casefold()
            members = [str(item).casefold() for item in assertion.get("members", [])]
            for line in lines:
                lower = line.casefold()
                if port_channel not in lower:
                    continue
                if protocol and protocol not in lower:
                    continue
                if any(member not in lower for member in members):
                    continue
                return True
            return False

        if kind == "hsrp":
            interface = str(assertion.get("interface", "")).casefold()
            state = str(assertion.get("state", "Active")).casefold()
            virtual_ip = str(assertion.get("virtual_ip", ""))
            for line in lines:
                lower = line.casefold()
                if interface and interface not in lower:
                    continue
                if state and state not in lower:
                    continue
                if virtual_ip and virtual_ip not in line:
                    continue
                return True
            return False

        if kind == "cdp_neighbor":
            device_id = str(assertion.get("device_id", "")).casefold()
            local_interface = str(assertion.get("local_interface", "")).casefold()
            for line in lines:
                lower = line.casefold()
                if device_id and device_id not in lower:
                    continue
                if local_interface and local_interface not in lower:
                    continue
                return True
            return False

        raise ValueError(f"Unsupported validation assertion type: {kind}")

    @classmethod
    def _expected_assertions(cls, check):
        assertions = list(check.get("assertions", []))
        if assertions:
            return assertions
        return [
            {"type": "contains", "value": token, "label": str(token)}
            for token in check.get("contains", [])
        ]

    @classmethod
    def _suggest_remediation(cls, check, missing):
        if not missing:
            return []
        if check.get("remediation"):
            return [str(command) for command in check["remediation"]]

        command = cls._normalized_search_text(check.get("command", ""))
        expected = [str(item) for item in check.get("contains", [])]
        if "running-config | include hostname" in command:
            hostname_line = next(
                (item for item in expected if item.lower().startswith("hostname ")),
                "hostname <EXPECTED-HOSTNAME>",
            )
            return ["configure terminal", hostname_line, "end", "write memory"]
        if command == "show ip ssh":
            return [
                "configure terminal",
                "ip domain-name ccna.lab",
                "username admin privilege 15 secret CCNAadmin!",
                "crypto key generate rsa modulus 2048",
                "ip ssh version 2",
                "line vty 0 4",
                "login local",
                "transport input ssh",
                "end",
                "write memory",
            ]
        if command == "show vlan brief":
            return ["configure terminal", "vlan <VLAN-ID>", "name <VLAN-NAME>", "end"]
        if command == "show interfaces trunk":
            return [
                "configure terminal",
                "interface <TRUNK-INTERFACE>",
                "switchport mode trunk",
                "switchport trunk native vlan <NATIVE-VLAN>",
                "end",
            ]
        if command == "show etherchannel summary":
            return [
                "configure terminal",
                "interface range <LINK-1>,<LINK-2>",
                "channel-group 1 mode active",
                "interface port-channel 1",
                "switchport mode trunk",
                "end",
            ]
        if command == "show ip ospf neighbor":
            return [
                "configure terminal",
                "router ospf <PROCESS-ID>",
                "network <NETWORK> <WILDCARD> area 0",
                "end",
            ]
        if "show ip interface brief" in command:
            return [
                "configure terminal",
                "interface <EXPECTED-INTERFACE>",
                "ip address <EXPECTED-IP> <SUBNET-MASK>",
                "no shutdown",
                "end",
            ]
        return []

    @classmethod
    def validate_output(cls, check, output):
        cleaned = cls.clean_output(check.get("command", ""), output)
        assertions = cls._expected_assertions(check)
        matched = []
        missing = []
        for assertion in assertions:
            label = cls._assertion_label(assertion)
            if cls._evaluate_assertion(assertion, cleaned):
                matched.append(label)
            else:
                missing.append(label)
        expected = [cls._assertion_label(item) for item in assertions]
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
