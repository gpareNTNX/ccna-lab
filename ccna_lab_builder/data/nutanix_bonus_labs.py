"""Nutanix bonus labs derived from user-supplied Nutanix documentation.

The source document is not redistributed. The lab below is an educational EVE-NG
adaptation of Nutanix KB-2455 (Cisco Nexus Best Practices, modified 2026-05-06).
"""


def NX(name, left, top):
    return {
        "name": name,
        "template": "nxosv9k",
        "left": left,
        "top": top,
        "interfaces": 8,
        "cpu": 2,
        "ram": "8192",
        "console": "telnet",
        "icon": "Switch.png",
    }


def P(name, left, top):
    return {
        "name": name,
        "template": "vpcs",
        "left": left,
        "top": top,
        "interfaces": 1,
        "icon": "Desktop.png",
    }


def L(a, ai, b, bi, name):
    return {"a": a, "a_if": ai, "b": b, "b_if": bi, "name": name}


def nutanix_bonus_labs():
    return [
        {
            "id": "NTNX-B01",
            "name": "Cisco Nexus Best Practices for Nutanix",
            "schema_version": 2,
            "catalog": "nutanix_bonus",
            "pack": "Bonus Nutanix",
            "buildable": True,
            "domain": "Nutanix Physical Networking",
            "difficulty": "Advanced",
            "minutes": 75,
            "source_basis": [
                "Nutanix KB-2455 — Cisco Nexus Best Practices",
                "Article modified May 6, 2026",
            ],
            "objective": (
                "Build the switch-side portion of a Nutanix dual-homed design on a Cisco "
                "Nexus vPC pair, then validate the VLAN, trunk, vPC and LACP practices "
                "described in Nutanix KB-2455."
            ),
            "tasks": [
                "Initialize both Nexus 9000v nodes. For this training lab use admin / NutanixLab! when NX-OS asks for credentials.",
                "Enable the vPC and LACP features on N9K-01 and N9K-02 and create VLANs 10, 20, 30 and 40.",
                "Use Ethernet1/3 as a dedicated routed vPC peer-keepalive link: 192.0.2.1/30 on N9K-01 and 192.0.2.2/30 on N9K-02.",
                "Build port-channel100 from Ethernet1/1-2 on both switches and make it the vPC peer-link carrying VLANs 10,20,30,40.",
                "Create vPC domain 10, configure peer-keepalive, and configure delay restore 450 as the lab value for reconvergence protection.",
                "Build port-channel3000 / vPC 3000 toward the simulated NTNX-AHV-01 uplinks. Use native VLAN 10 and allow VLANs 20,30,40.",
                "On port-channel3000 configure spanning-tree port type edge trunk and no lacp suspend-individual.",
                "Use Ethernet1/4 as the host-facing member on each Nexus, configure lacp rate fast, and add it to channel-group 3000 mode active.",
                "Design checkpoint: for a non-vPC host attachment on a vPC pair, explain why vpc orphan-port suspend is recommended on host-facing interfaces.",
                "Design checkpoint: explain why 10 GbE Nexus FEX attachment is not recommended for Nutanix data traffic and prefer direct low-latency, non-blocking, line-rate switchports.",
                "Security/operations checkpoint: do not apply port-security to Nutanix host-facing ports, keep IPv6 link-local communication available, and use port type edge on host-facing links.",
            ],
            "notes": [
                "The two VPCS endpoints represent the left/right Nutanix uplinks visually; VPCS does not emulate an AHV LACP bond. Validation is intentionally switch-side.",
                "KB-2455 examples are educational examples, not a universal production configuration. Validate a real deployment with the network vendor/Cisco TAC and the actual NX-OS release.",
                "The KB example uses Ethernet1/20 for the Nutanix host. This virtual lab uses Ethernet1/4 to reduce the number of emulated interfaces while preserving the design intent.",
                "Nutanix KB-2455 does not recommend 10 GbE FEX/2K attachment for Nutanix data ports because of oversubscription, east/west limitations and small buffers.",
                "The KB recommends LACP fast on both AHV and the physical switch when LACP is used, reducing failure detection compared with slow timers.",
            ],
            "checks": [
                {
                    "node": "N9K-01",
                    "command": "show running-config | include ^feature",
                    "contains": ["feature vpc", "feature lacp"],
                },
                {
                    "node": "N9K-02",
                    "command": "show running-config | include ^feature",
                    "contains": ["feature vpc", "feature lacp"],
                },
                {
                    "node": "N9K-01",
                    "command": "show vlan brief",
                    "contains": ["10", "20", "30", "40"],
                },
                {
                    "node": "N9K-02",
                    "command": "show vlan brief",
                    "contains": ["10", "20", "30", "40"],
                },
                {
                    "node": "N9K-01",
                    "command": "show running-config | section ^vpc.domain",
                    "contains": [
                        "vpc domain 10",
                        "peer-keepalive destination 192.0.2.2 source 192.0.2.1",
                        "delay restore 450",
                    ],
                },
                {
                    "node": "N9K-02",
                    "command": "show running-config | section ^vpc.domain",
                    "contains": [
                        "vpc domain 10",
                        "peer-keepalive destination 192.0.2.1 source 192.0.2.2",
                        "delay restore 450",
                    ],
                },
                {
                    "node": "N9K-01",
                    "command": "show running-config interface port-channel100",
                    "contains": [
                        "switchport mode trunk",
                        "switchport trunk allowed vlan 10,20,30,40",
                        "vpc peer-link",
                    ],
                },
                {
                    "node": "N9K-02",
                    "command": "show running-config interface port-channel100",
                    "contains": [
                        "switchport mode trunk",
                        "switchport trunk allowed vlan 10,20,30,40",
                        "vpc peer-link",
                    ],
                },
                {
                    "node": "N9K-01",
                    "command": "show running-config interface port-channel3000",
                    "contains": [
                        "switchport mode trunk",
                        "switchport trunk allowed vlan 20,30,40",
                        "switchport trunk native vlan 10",
                        "spanning-tree port type edge trunk",
                        "no lacp suspend-individual",
                        "vpc 3000",
                    ],
                },
                {
                    "node": "N9K-02",
                    "command": "show running-config interface port-channel3000",
                    "contains": [
                        "switchport mode trunk",
                        "switchport trunk allowed vlan 20,30,40",
                        "switchport trunk native vlan 10",
                        "spanning-tree port type edge trunk",
                        "no lacp suspend-individual",
                        "vpc 3000",
                    ],
                },
                {
                    "node": "N9K-01",
                    "command": "show running-config interface Ethernet1/4",
                    "contains": ["lacp rate fast", "channel-group 3000 mode active"],
                },
                {
                    "node": "N9K-02",
                    "command": "show running-config interface Ethernet1/4",
                    "contains": ["lacp rate fast", "channel-group 3000 mode active"],
                },
            ],
            "topology": {
                "nodes": [
                    NX("N9K-01", "28%", "34%"),
                    NX("N9K-02", "68%", "34%"),
                    P("NTNX-AHV-01-ETH2", "28%", "78%"),
                    P("NTNX-AHV-01-ETH3", "68%", "78%"),
                ],
                "links": [
                    L("N9K-01", "Ethernet1/1", "N9K-02", "Ethernet1/1", "VPC-PEER-LINK-1"),
                    L("N9K-01", "Ethernet1/2", "N9K-02", "Ethernet1/2", "VPC-PEER-LINK-2"),
                    L("N9K-01", "Ethernet1/3", "N9K-02", "Ethernet1/3", "VPC-KEEPALIVE"),
                    L("N9K-01", "Ethernet1/4", "NTNX-AHV-01-ETH2", "eth0", "NTNX-AHV-01-ETH2"),
                    L("N9K-02", "Ethernet1/4", "NTNX-AHV-01-ETH3", "eth0", "NTNX-AHV-01-ETH3"),
                ],
            },
        }
    ]
