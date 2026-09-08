"""Additional original Nutanix/data-center labs for NX-OSv9K.

These scenarios are original educational exercises. They are inspired by common data-center
lab topics, including the public EVE-NG Lab Library, but do not redistribute EVE-NG lab files.
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


def nutanix_bonus_expansion_labs():
    """Return additional NX-OSv9K labs for the Bonus Nutanix workspace."""
    return [
        {
            "id": "NTNX-B02",
            "name": "Nexus vPC Operations and Failure Recovery",
            "schema_version": 2,
            "catalog": "nutanix_bonus",
            "pack": "Bonus Nutanix",
            "buildable": True,
            "domain": "Nutanix Physical Networking",
            "difficulty": "Advanced",
            "minutes": 70,
            "source_basis": [
                "Public EVE-NG Cisco Data Center lab topics",
                "Original Nutanix-oriented vPC operations exercise",
            ],
            "objective": (
                "Build a compact Nexus vPC pair for dual-homed Nutanix-style uplinks, "
                "then practice operational verification and controlled failure recovery."
            ),
            "tasks": [
                "Initialize both Nexus nodes with the training credentials admin / NutanixLab!.",
                "Enable feature vpc and feature lacp on both switches.",
                "Create VLANs 10, 20 and 30 and allow them across the peer-link.",
                "Use Ethernet1/3 as the routed peer-keepalive link: 192.0.2.1/30 and 192.0.2.2/30.",
                "Build port-channel100 from Ethernet1/1-2 and configure it as the vPC peer-link.",
                "Create vPC domain 20 and configure reciprocal peer-keepalive addresses.",
                "Build port-channel200 / vPC 200 toward the simulated Nutanix uplinks on Ethernet1/4.",
                "Configure the host-facing bundle as an edge trunk and use LACP active with fast timers.",
                "Verify show vpc, show port-channel summary and show lacp neighbor before introducing a failure.",
                "Shut one peer-link member, verify the peer-link remains operational, then restore it.",
                "Shut the host-facing member on one peer, observe vPC state, then restore it and document recovery.",
            ],
            "notes": [
                "The VPCS endpoints are topology stubs; validation is intentionally switch-side.",
                "This lab focuses on operational behavior and recovery rather than reproducing a production Nutanix host bond.",
                "Use the failure steps only inside this training lab.",
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
                    "command": "show running-config | section ^vpc.domain",
                    "contains": [
                        "vpc domain 20",
                        "peer-keepalive destination 192.0.2.2 source 192.0.2.1",
                    ],
                },
                {
                    "node": "N9K-02",
                    "command": "show running-config | section ^vpc.domain",
                    "contains": [
                        "vpc domain 20",
                        "peer-keepalive destination 192.0.2.1 source 192.0.2.2",
                    ],
                },
                {
                    "node": "N9K-01",
                    "command": "show running-config interface port-channel100",
                    "contains": ["switchport mode trunk", "vpc peer-link"],
                },
                {
                    "node": "N9K-02",
                    "command": "show running-config interface port-channel100",
                    "contains": ["switchport mode trunk", "vpc peer-link"],
                },
                {
                    "node": "N9K-01",
                    "command": "show running-config interface port-channel200",
                    "contains": [
                        "switchport mode trunk",
                        "spanning-tree port type edge trunk",
                        "vpc 200",
                    ],
                },
                {
                    "node": "N9K-02",
                    "command": "show running-config interface port-channel200",
                    "contains": [
                        "switchport mode trunk",
                        "spanning-tree port type edge trunk",
                        "vpc 200",
                    ],
                },
                {
                    "node": "N9K-01",
                    "command": "show running-config interface Ethernet1/4",
                    "contains": ["lacp rate fast", "channel-group 200 mode active"],
                },
                {
                    "node": "N9K-02",
                    "command": "show running-config interface Ethernet1/4",
                    "contains": ["lacp rate fast", "channel-group 200 mode active"],
                },
            ],
            "topology": {
                "nodes": [
                    NX("N9K-01", "28%", "32%"),
                    NX("N9K-02", "68%", "32%"),
                    P("NTNX-UPLINK-A", "28%", "78%"),
                    P("NTNX-UPLINK-B", "68%", "78%"),
                ],
                "links": [
                    L("N9K-01", "Ethernet1/1", "N9K-02", "Ethernet1/1", "VPC-PEER-1"),
                    L("N9K-01", "Ethernet1/2", "N9K-02", "Ethernet1/2", "VPC-PEER-2"),
                    L("N9K-01", "Ethernet1/3", "N9K-02", "Ethernet1/3", "VPC-KEEPALIVE"),
                    L("N9K-01", "Ethernet1/4", "NTNX-UPLINK-A", "eth0", "HOST-A"),
                    L("N9K-02", "Ethernet1/4", "NTNX-UPLINK-B", "eth0", "HOST-B"),
                ],
            },
        },
        {
            "id": "NTNX-B03",
            "name": "VXLAN BGP EVPN Fundamentals for Nutanix Networks",
            "schema_version": 2,
            "catalog": "nutanix_bonus",
            "pack": "Bonus Nutanix",
            "buildable": True,
            "domain": "Data Center Fabric",
            "difficulty": "Expert",
            "minutes": 95,
            "source_basis": [
                "Public EVE-NG Nexus 9000v VXLAN/BGP EVPN lab topic",
                "Original compact two-VTEP implementation for this project",
            ],
            "objective": (
                "Build a compact two-VTEP NX-OSv9K fabric with an OSPF underlay and "
                "BGP EVPN overlay, then map a Nutanix-style host VLAN to a VXLAN VNI."
            ),
            "tasks": [
                "Initialize both Nexus nodes with admin / NutanixLab!.",
                "Enable feature ospf, feature bgp, feature nv overlay and nv overlay evpn.",
                "Convert Ethernet1/1 on both switches to a routed underlay link using 10.255.0.1/30 and 10.255.0.2/30.",
                "Create Loopback0 as the router ID: 10.255.255.1/32 and 10.255.255.2/32.",
                "Create Loopback1 as the VTEP source: 10.254.0.1/32 and 10.254.0.2/32.",
                "Run OSPF process UNDERLAY in area 0 across Ethernet1/1 and both loopbacks.",
                "Run BGP AS 65000 and establish an iBGP EVPN session between Loopback0 addresses.",
                "Activate the l2vpn evpn address family and send-community extended toward the peer.",
                "Create VLAN 10, map it to VNI 10010, and configure Ethernet1/2 as an edge access port in VLAN 10.",
                "Create interface nve1 sourced from Loopback1 and add member VNI 10010 with BGP ingress replication.",
                "Create EVPN VNI 10010 as L2 with route-target import/export auto.",
                "Verify OSPF reachability, BGP EVPN peering, NVE state and learned EVPN routes.",
            ],
            "notes": [
                "This is a compact educational VXLAN/EVPN lab, not a production reference architecture.",
                "Both VPCS endpoints represent workload attachment points; VPCS does not emulate AHV switching or bonding.",
                "NX-OS syntax can vary by release. The current project targets the nxosv9k image family detected by EVE-NG.",
            ],
            "checks": [
                {
                    "node": "VTEP-01",
                    "command": "show running-config | include ^feature|^nv overlay",
                    "contains": [
                        "feature ospf",
                        "feature bgp",
                        "feature nv overlay",
                        "nv overlay evpn",
                    ],
                },
                {
                    "node": "VTEP-02",
                    "command": "show running-config | include ^feature|^nv overlay",
                    "contains": [
                        "feature ospf",
                        "feature bgp",
                        "feature nv overlay",
                        "nv overlay evpn",
                    ],
                },
                {
                    "node": "VTEP-01",
                    "command": "show running-config interface nve1",
                    "contains": [
                        "source-interface loopback1",
                        "member vni 10010",
                        "ingress-replication protocol bgp",
                    ],
                },
                {
                    "node": "VTEP-02",
                    "command": "show running-config interface nve1",
                    "contains": [
                        "source-interface loopback1",
                        "member vni 10010",
                        "ingress-replication protocol bgp",
                    ],
                },
                {
                    "node": "VTEP-01",
                    "command": "show running-config | section ^router.bgp",
                    "contains": ["router bgp 65000", "address-family l2vpn evpn"],
                },
                {
                    "node": "VTEP-02",
                    "command": "show running-config | section ^router.bgp",
                    "contains": ["router bgp 65000", "address-family l2vpn evpn"],
                },
                {
                    "node": "VTEP-01",
                    "command": "show running-config vlan 10",
                    "contains": ["vn-segment 10010"],
                },
                {
                    "node": "VTEP-02",
                    "command": "show running-config vlan 10",
                    "contains": ["vn-segment 10010"],
                },
            ],
            "topology": {
                "nodes": [
                    NX("VTEP-01", "28%", "35%"),
                    NX("VTEP-02", "68%", "35%"),
                    P("NTNX-WORKLOAD-A", "28%", "80%"),
                    P("NTNX-WORKLOAD-B", "68%", "80%"),
                ],
                "links": [
                    L("VTEP-01", "Ethernet1/1", "VTEP-02", "Ethernet1/1", "UNDERLAY"),
                    L("VTEP-01", "Ethernet1/2", "NTNX-WORKLOAD-A", "eth0", "VLAN10-A"),
                    L("VTEP-02", "Ethernet1/2", "NTNX-WORKLOAD-B", "eth0", "VLAN10-B"),
                ],
            },
        },
    ]
