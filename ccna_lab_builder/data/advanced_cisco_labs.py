"""Original advanced Cisco labs inspired by topics in the public EVE-NG Lab Library.

No EVE-NG lab archive, workbook, or vendor image is redistributed. These scenarios are
original exercises built for this application's existing IOSv/IOSvL2 workflow.
"""


def R(name, left, top):
    return {
        "name": name,
        "template": "vios",
        "left": left,
        "top": top,
        "interfaces": 8,
    }


def S(name, left, top):
    return {
        "name": name,
        "template": "viosl2",
        "left": left,
        "top": top,
        "interfaces": 8,
    }


def P(name, left, top):
    return {
        "name": name,
        "template": "vpcs",
        "left": left,
        "top": top,
        "interfaces": 1,
    }


def L(a, ai, b, bi, name=None):
    item = {"a": a, "a_if": ai, "b": b, "b_if": bi}
    if name:
        item["name"] = name
    return item


def A(
    lab_id,
    name,
    domain,
    objective,
    tasks,
    nodes,
    links,
    checks,
    minutes=55,
    difficulty="Advanced",
):
    return {
        "id": lab_id,
        "name": name,
        "schema_version": 2,
        "catalog": "challenge",
        "pack": "Advanced Cisco",
        "source_basis": [
            "Public EVE-NG Lab Library topic index",
            "Original implementation for CCNA EVE Lab Builder",
        ],
        "objective": objective,
        "tasks": tasks,
        "checks": checks,
        "minutes": minutes,
        "difficulty": difficulty,
        "domain": domain,
        "buildable": True,
        "topology": {"nodes": nodes, "links": links},
    }


def advanced_cisco_labs():
    """Return advanced labs kept separate from numeric CCNA labs 01-37."""
    return [
        A(
            "ADV-C01",
            "MSTP Region and Root Control",
            "Network Access",
            "Build a three-switch Multiple Spanning Tree region and deliberately place "
            "different MST instances on different roots.",
            [
                "Create VLANs 10, 20 and 30 on all switches.",
                "Configure MST region LAB, revision 1, on all three switches.",
                "Map VLANs 10 and 20 to MST instance 1 and VLAN 30 to instance 2.",
                "Make SW1-CORE the primary root for MST 1.",
                "Make SW2-DIST the primary root for MST 2.",
                "Verify that all switches report the same region digest and mappings.",
            ],
            [
                S("SW1-CORE", "20%", "25%"),
                S("SW2-DIST", "70%", "25%"),
                S("SW3-ACCESS", "45%", "70%"),
            ],
            [
                L("SW1-CORE", "Gi0/0", "SW2-DIST", "Gi0/0"),
                L("SW1-CORE", "Gi0/1", "SW3-ACCESS", "Gi0/0"),
                L("SW2-DIST", "Gi0/1", "SW3-ACCESS", "Gi0/1"),
            ],
            [
                {
                    "node": "SW1-CORE",
                    "command": "show running-config",
                    "contains": [
                        "spanning-tree mode mst",
                        "name LAB",
                        "revision 1",
                        "instance 1 vlan 10, 20",
                        "instance 2 vlan 30",
                        "spanning-tree mst 1 root primary",
                    ],
                },
                {
                    "node": "SW2-DIST",
                    "command": "show running-config",
                    "contains": [
                        "spanning-tree mode mst",
                        "name LAB",
                        "revision 1",
                        "spanning-tree mst 2 root primary",
                    ],
                },
            ],
            minutes=50,
        ),
        A(
            "ADV-C02",
            "VTP Domain Operations",
            "Network Access",
            "Practice controlled VTP server/client operation across a trunked switching "
            "domain without changing the core CCNA catalog.",
            [
                "Build 802.1Q trunks between SW1-SERVER, SW2-CLIENT and SW3-CLIENT.",
                "Use VTP domain EVE-LAB and VTP version 2 on all switches.",
                "Configure SW1-SERVER in VTP server mode.",
                "Configure SW2-CLIENT and SW3-CLIENT in VTP client mode.",
                "Create VLANs 110, 120 and 130 on the server and verify propagation.",
                "Record the VTP revision before and after the VLAN change.",
            ],
            [
                S("SW1-SERVER", "18%", "38%"),
                S("SW2-CLIENT", "48%", "38%"),
                S("SW3-CLIENT", "78%", "38%"),
            ],
            [
                L("SW1-SERVER", "Gi0/0", "SW2-CLIENT", "Gi0/0"),
                L("SW2-CLIENT", "Gi0/1", "SW3-CLIENT", "Gi0/0"),
            ],
            [
                {
                    "node": "SW1-SERVER",
                    "command": "show running-config | include ^vtp",
                    "contains": ["vtp domain EVE-LAB", "vtp mode server"],
                },
                {
                    "node": "SW2-CLIENT",
                    "command": "show running-config | include ^vtp",
                    "contains": ["vtp domain EVE-LAB", "vtp mode client"],
                },
                {
                    "node": "SW3-CLIENT",
                    "command": "show running-config | include ^vtp",
                    "contains": ["vtp domain EVE-LAB", "vtp mode client"],
                },
            ],
            minutes=45,
        ),
        A(
            "ADV-C03",
            "SPAN and RSPAN Monitoring",
            "Network Operations",
            "Configure a local SPAN source and extend mirrored traffic across a dedicated "
            "RSPAN VLAN to a remote analyzer port.",
            [
                "Create RSPAN VLAN 999 on SW1-SOURCE and SW2-ANALYZER.",
                "Trunk VLAN 999 between the switches.",
                "Use SW1 Gi0/1 as the monitored source interface.",
                "Send the mirrored session into remote VLAN 999.",
                "On SW2, source the remote session from VLAN 999.",
                "Use SW2 Gi0/2 as the analyzer destination port.",
                "Verify both monitor sessions from the CLI.",
            ],
            [
                S("SW1-SOURCE", "30%", "35%"),
                S("SW2-ANALYZER", "70%", "35%"),
                P("TRAFFIC-SOURCE", "20%", "76%"),
                P("ANALYZER", "80%", "76%"),
            ],
            [
                L("SW1-SOURCE", "Gi0/0", "SW2-ANALYZER", "Gi0/0", "RSPAN-TRUNK"),
                L("SW1-SOURCE", "Gi0/1", "TRAFFIC-SOURCE", "eth0"),
                L("SW2-ANALYZER", "Gi0/2", "ANALYZER", "eth0"),
            ],
            [
                {
                    "node": "SW1-SOURCE",
                    "command": "show running-config | include monitor session",
                    "contains": [
                        "monitor session 1 source interface Gi0/1",
                        "monitor session 1 destination remote vlan 999",
                    ],
                },
                {
                    "node": "SW2-ANALYZER",
                    "command": "show running-config | include monitor session",
                    "contains": [
                        "monitor session 2 source remote vlan 999",
                        "monitor session 2 destination interface Gi0/2",
                    ],
                },
            ],
            minutes=45,
        ),
        A(
            "ADV-C04",
            "Multi-Area OSPFv2",
            "IP Connectivity",
            "Build a three-router OSPFv2 topology with an ABR between area 0 and area 10 "
            "and verify inter-area reachability.",
            [
                "Address R1-R2 with 10.0.12.0/30 and R2-R3 with 10.0.23.0/30.",
                "Create Loopback0 on every router using 1.1.1.1/32, 2.2.2.2/32 and 3.3.3.3/32.",
                "Place the R1-R2 link and R1 loopback in area 0.",
                "Use R2 as the ABR and place the R2-R3 link plus R3 loopback in area 10.",
                "Set deterministic router IDs and make point-to-point links passive only when appropriate.",
                "Verify FULL adjacencies and O IA routes across the ABR.",
            ],
            [
                R("R1-BACKBONE", "18%", "48%"),
                R("R2-ABR", "50%", "48%"),
                R("R3-AREA10", "82%", "48%"),
            ],
            [
                L("R1-BACKBONE", "Gi0/0", "R2-ABR", "Gi0/0"),
                L("R2-ABR", "Gi0/1", "R3-AREA10", "Gi0/0"),
            ],
            [
                {
                    "node": "R1-BACKBONE",
                    "command": "show ip ospf neighbor",
                    "contains": ["FULL"],
                },
                {
                    "node": "R2-ABR",
                    "command": "show ip ospf neighbor",
                    "contains": ["FULL"],
                },
                {
                    "node": "R1-BACKBONE",
                    "command": "show ip route ospf",
                    "contains": ["O IA"],
                },
            ],
            minutes=60,
        ),
        A(
            "ADV-C05",
            "OSPF ABR Route Summarization",
            "IP Connectivity",
            "Summarize multiple area-10 networks at an OSPF ABR and compare the backbone "
            "routing table before and after aggregation.",
            [
                "Build area 0 between R1-BACKBONE and R2-ABR.",
                "Build area 10 between R2-ABR and R3-AREA10.",
                "Create four /24 Loopback networks on R3 from 10.10.0.0/24 through 10.10.3.0/24.",
                "Advertise all four loopbacks in area 10.",
                "Configure area 10 range 10.10.0.0 255.255.252.0 on R2-ABR.",
                "Verify the backbone sees the /22 summary rather than four component routes.",
            ],
            [
                R("R1-BACKBONE", "18%", "48%"),
                R("R2-ABR", "50%", "48%"),
                R("R3-AREA10", "82%", "48%"),
            ],
            [
                L("R1-BACKBONE", "Gi0/0", "R2-ABR", "Gi0/0"),
                L("R2-ABR", "Gi0/1", "R3-AREA10", "Gi0/0"),
            ],
            [
                {
                    "node": "R2-ABR",
                    "command": "show running-config | section router ospf",
                    "contains": ["area 10 range 10.10.0.0 255.255.252.0"],
                },
                {
                    "node": "R1-BACKBONE",
                    "command": "show ip route ospf",
                    "contains": ["10.10.0.0/22"],
                },
            ],
            minutes=55,
        ),
        A(
            "ADV-C06",
            "Multi-Area OSPFv3",
            "IPv6 / IP Connectivity",
            "Extend the multi-area routing exercise to IPv6 with OSPFv3, deterministic "
            "router IDs, and inter-area IPv6 reachability.",
            [
                "Enable ipv6 unicast-routing on all routers.",
                "Use 2001:db8:12::/64 between R1 and R2 and 2001:db8:23::/64 between R2 and R3.",
                "Create one /128 IPv6 loopback on each router.",
                "Run OSPFv3 process 10 with router IDs 1.1.1.1, 2.2.2.2 and 3.3.3.3.",
                "Place the R1-R2 side in area 0 and the R2-R3 side in area 10.",
                "Verify FULL OSPFv3 neighbors and inter-area IPv6 routes.",
            ],
            [
                R("R1-V6", "18%", "48%"),
                R("R2-ABR", "50%", "48%"),
                R("R3-V6", "82%", "48%"),
            ],
            [
                L("R1-V6", "Gi0/0", "R2-ABR", "Gi0/0"),
                L("R2-ABR", "Gi0/1", "R3-V6", "Gi0/0"),
            ],
            [
                {
                    "node": "R1-V6",
                    "command": "show ipv6 ospf neighbor",
                    "contains": ["FULL"],
                },
                {
                    "node": "R2-ABR",
                    "command": "show ipv6 ospf neighbor",
                    "contains": ["FULL"],
                },
                {
                    "node": "R3-V6",
                    "command": "show running-config | include ipv6 unicast-routing",
                    "contains": ["ipv6 unicast-routing"],
                },
            ],
            minutes=60,
        ),
        A(
            "ADV-C07",
            "EIGRP Fundamentals",
            "Advanced Routing",
            "Build a small EIGRP autonomous system, form neighbors, advertise loopbacks, "
            "and verify D routes end to end.",
            [
                "Address the R1-R2 and R2-R3 routed links with /30 networks.",
                "Create Loopback0 on every router.",
                "Run classic EIGRP AS 100 on all routers.",
                "Disable automatic summarization if the image exposes that behavior.",
                "Make Loopback0 passive while keeping routed links active.",
                "Verify EIGRP adjacencies and learned D routes.",
            ],
            [
                R("R1", "18%", "48%"),
                R("R2", "50%", "48%"),
                R("R3", "82%", "48%"),
            ],
            [
                L("R1", "Gi0/0", "R2", "Gi0/0"),
                L("R2", "Gi0/1", "R3", "Gi0/0"),
            ],
            [
                {
                    "node": "R1",
                    "command": "show ip eigrp neighbors",
                    "contains": ["R2"],
                },
                {
                    "node": "R2",
                    "command": "show running-config | section router eigrp",
                    "contains": ["router eigrp 100"],
                },
                {
                    "node": "R3",
                    "command": "show ip route eigrp",
                    "contains": ["D"],
                },
            ],
            minutes=55,
        ),
        A(
            "ADV-C08",
            "eBGP Fundamentals",
            "Advanced Routing",
            "Build a three-AS eBGP chain, advertise loopbacks, and verify that routes "
            "cross multiple autonomous systems.",
            [
                "Use AS 65001 on R1, AS 65002 on R2 and AS 65003 on R3.",
                "Address R1-R2 and R2-R3 with separate /30 transit networks.",
                "Create Loopback0 on each router and advertise it into BGP.",
                "Configure direct eBGP neighbors on each transit link.",
                "Verify both R2 sessions are established.",
                "Verify R1 learns the R3 loopback and R3 learns the R1 loopback through BGP.",
            ],
            [
                R("R1-AS65001", "18%", "48%"),
                R("R2-AS65002", "50%", "48%"),
                R("R3-AS65003", "82%", "48%"),
            ],
            [
                L("R1-AS65001", "Gi0/0", "R2-AS65002", "Gi0/0"),
                L("R2-AS65002", "Gi0/1", "R3-AS65003", "Gi0/0"),
            ],
            [
                {
                    "node": "R1-AS65001",
                    "command": "show running-config | section router bgp",
                    "contains": ["router bgp 65001"],
                },
                {
                    "node": "R2-AS65002",
                    "command": "show running-config | section router bgp",
                    "contains": ["router bgp 65002", "remote-as 65001", "remote-as 65003"],
                },
                {
                    "node": "R3-AS65003",
                    "command": "show running-config | section router bgp",
                    "contains": ["router bgp 65003"],
                },
            ],
            minutes=65,
        ),
    ]
