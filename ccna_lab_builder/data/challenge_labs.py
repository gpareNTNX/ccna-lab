"""Original EVE-NG challenge adaptations based on concepts in the supplied PKT archive.

The Packet Tracer files themselves are not redistributed. Challenge IDs are deliberately
non-numeric so the stable CCNA catalog 01-37 remains untouched.
"""


def R(name, left, top):
    return {"name": name, "template": "vios", "left": left, "top": top, "interfaces": 8}


def S(name, left, top):
    return {"name": name, "template": "viosl2", "left": left, "top": top, "interfaces": 8}


def P(name, left, top):
    return {"name": name, "template": "vpcs", "left": left, "top": top, "interfaces": 1}


def L(a, ai, b, bi, name=None):
    item = {"a": a, "a_if": ai, "b": b, "b_if": bi}
    if name:
        item["name"] = name
    return item


def C(cid, name, source, objective, tasks, nodes, links, checks, minutes=45, difficulty="Intermediate", domain="Network Access"):
    return {
        "id": cid, "name": name, "schema_version": 2, "catalog": "challenge",
        "pack": "Cisco Challenge", "source_basis": source, "objective": objective,
        "tasks": tasks, "checks": checks, "minutes": minutes, "difficulty": difficulty,
        "domain": domain, "buildable": True, "topology": {"nodes": nodes, "links": links},
    }


def challenge_labs():
    return [
        C("PT-C01", "Rapid-PVST+ Root Election", ["STP3.pkt", "STP.pkt"],
          "Control Rapid-PVST+ root placement across a redundant four-switch domain.",
          ["Create VLANs 10, 20 and 99.", "Enable rapid-pvst.", "Make SW1-CORE root for VLANs 10/99 and SW2-DIST root for VLAN 20.", "Verify root election and forwarding paths."],
          [S("SW1-CORE","22%","25%"),S("SW2-DIST","62%","25%"),S("SW3-ACCESS","22%","68%"),S("SW4-ACCESS","62%","68%")],
          [L("SW1-CORE","Gi0/0","SW2-DIST","Gi0/0"),L("SW1-CORE","Gi0/1","SW3-ACCESS","Gi0/0"),L("SW2-DIST","Gi0/1","SW4-ACCESS","Gi0/0"),L("SW3-ACCESS","Gi0/1","SW4-ACCESS","Gi0/1"),L("SW1-CORE","Gi0/2","SW4-ACCESS","Gi0/2")],
          [{"node":"SW1-CORE","command":"show spanning-tree root","contains":["Vl10","Vl99"]},{"node":"SW2-DIST","command":"show spanning-tree root","contains":["Vl20"]}], 35),
        C("PT-C02", "STP Protection and Edge Safety", ["STP2.pkt"],
          "Harden a Rapid-PVST+ topology with PortFast, BPDU Guard and Root Guard.",
          ["Create VLAN 10 and trunk inter-switch links.", "Make SW1-CORE root for VLAN 10.", "Apply PortFast and BPDU Guard to PC-facing ports.", "Apply Root Guard on the designated SW1 downstream link."],
          [S("SW1-CORE","40%","20%"),S("SW2-DIST","20%","55%"),S("SW3-ACCESS","62%","55%"),P("PC-A","12%","82%"),P("PC-B","76%","82%")],
          [L("SW1-CORE","Gi0/0","SW2-DIST","Gi0/0"),L("SW1-CORE","Gi0/1","SW3-ACCESS","Gi0/0"),L("SW2-DIST","Gi0/1","SW3-ACCESS","Gi0/1"),L("SW2-DIST","Gi0/2","PC-A","eth0"),L("SW3-ACCESS","Gi0/2","PC-B","eth0")],
          [{"node":"SW2-DIST","command":"show running-config interface GigabitEthernet0/2","contains":["spanning-tree portfast","spanning-tree bpduguard enable"]},{"node":"SW1-CORE","command":"show running-config interface GigabitEthernet0/1","contains":["spanning-tree guard root"]}], 35),
        C("PT-C03", "STP VLAN Load Balancing", ["STP Load Balancing.pkt"],
          "Distribute STP root responsibility across redundant switches for different VLANs.",
          ["Create VLANs 10 and 20.", "Trunk every inter-switch link.", "Make SW1-CORE root for VLAN 10 and SW2-DIST root for VLAN 20.", "Verify forwarding paths."],
          [S("SW1-CORE","22%","24%"),S("SW2-DIST","62%","24%"),S("SW3-ACCESS","22%","68%"),S("SW4-ACCESS","62%","68%")],
          [L("SW1-CORE","Gi0/0","SW2-DIST","Gi0/0"),L("SW1-CORE","Gi0/1","SW3-ACCESS","Gi0/0"),L("SW1-CORE","Gi0/2","SW4-ACCESS","Gi0/0"),L("SW2-DIST","Gi0/1","SW3-ACCESS","Gi0/1"),L("SW2-DIST","Gi0/2","SW4-ACCESS","Gi0/1")],
          [{"node":"SW1-CORE","command":"show spanning-tree root","contains":["Vl10"]},{"node":"SW2-DIST","command":"show spanning-tree root","contains":["Vl20"]}], 40),
        C("PT-C04", "Router-on-a-Stick Challenge", ["Router on a stick.pkt"],
          "Provide inter-VLAN routing through a single 802.1Q router link.",
          ["Create VLANs 10 and 20 on SW1.", "Configure the R1-SW1 link as a trunk.", "Create R1 subinterfaces Gi0/0.10 and Gi0/0.20 with dot1Q encapsulation.", "Attach one VPCS endpoint to each VLAN and test reachability."],
          [R("R1","48%","24%"),S("SW1","48%","50%"),P("PC-A","24%","78%"),P("PC-B","72%","78%")],
          [L("R1","Gi0/0","SW1","Gi0/0"),L("SW1","Gi0/1","PC-A","eth0"),L("SW1","Gi0/2","PC-B","eth0")],
          [{"node":"R1","command":"show running-config interface GigabitEthernet0/0.10","contains":["encapsulation dot1Q 10"]},{"node":"R1","command":"show running-config interface GigabitEthernet0/0.20","contains":["encapsulation dot1Q 20"]},{"node":"SW1","command":"show interfaces trunk","contains":["Gi0/0"]}], 40, domain="IP Connectivity"),
        C("PT-C05", "SVI and Layer-3 Switching", ["SVI.pkt"],
          "Route user VLANs with IOSvL2 SVIs and a routed inter-switch path.",
          ["Enable ip routing on both multilayer switches.", "Create VLANs 10 and 20 and their SVIs.", "Use a routed link between the switches.", "Attach VPCS hosts and verify reachability."],
          [S("SW1-L3","30%","38%"),S("SW2-L3","66%","38%"),P("PC-A","18%","76%"),P("PC-B","78%","76%")],
          [L("SW1-L3","Gi0/0","SW2-L3","Gi0/0"),L("SW1-L3","Gi0/1","PC-A","eth0"),L("SW2-L3","Gi0/1","PC-B","eth0")],
          [{"node":"SW1-L3","command":"show running-config | include ^ip routing","contains":["ip routing"]},{"node":"SW1-L3","command":"show ip interface brief","contains":["Vlan10"]},{"node":"SW2-L3","command":"show ip interface brief","contains":["Vlan20"]}], 45, domain="IP Connectivity"),
        C("PT-C06", "OSPF Troubleshooting Challenge", ["OSPF Troubleshooting.pkt"],
          "Troubleshoot a four-router topology adapted to current single-area OSPFv2 practice.",
          ["Address every routed link.", "Place all routed links in OSPF area 0.", "Advertise Loopback0 on each router.", "Fix adjacency or route problems until all routers converge."],
          [R("R1","12%","48%"),R("R2","38%","24%"),R("R3","66%","24%"),R("R4","86%","48%")],
          [L("R1","Gi0/0","R2","Gi0/0"),L("R2","Gi0/1","R3","Gi0/0"),L("R3","Gi0/1","R4","Gi0/0"),L("R1","Gi0/1","R4","Gi0/1")],
          [{"node":"R1","command":"show ip ospf neighbor","contains":["FULL"]},{"node":"R2","command":"show ip ospf neighbor","contains":["FULL"]},{"node":"R3","command":"show ip ospf neighbor","contains":["FULL"]},{"node":"R4","command":"show ip ospf neighbor","contains":["FULL"]}], 55, "Advanced", "IP Connectivity"),
        C("PT-C07", "SOHO Services: DHCP, NAT and ACL", ["SOHO.pkt"],
          "Build a compact routed edge with DHCP, NAT/PAT and an IPv4 ACL.",
          ["Use 10.10.10.0/24 on the LAN.", "Configure EDGE DHCP pool LAN.", "Configure NAT inside/outside and PAT.", "Create an ACL matching the inside subnet.", "Use VPCS endpoints for basic reachability tests."],
          [R("EDGE","38%","42%"),R("ISP","69%","42%"),S("SW1-LAN","20%","42%"),P("PC-LAN","7%","67%"),P("PC-INET","87%","67%")],
          [L("PC-LAN","eth0","SW1-LAN","Gi0/1"),L("SW1-LAN","Gi0/0","EDGE","Gi0/0"),L("EDGE","Gi0/1","ISP","Gi0/0"),L("ISP","Gi0/1","PC-INET","eth0")],
          [{"node":"EDGE","command":"show running-config | include ip nat","contains":["ip nat inside","ip nat outside","ip nat inside source"]},{"node":"EDGE","command":"show ip dhcp pool","contains":["Pool LAN"]},{"node":"EDGE","command":"show access-lists","contains":["10.10.10.0"]}], 55, "Advanced", "IP Services / Security Fundamentals"),
        C("PT-C08", "Enterprise Switching Mega Challenge", ["VLANs---SpanningTreeProtocol.pkt", "STP.pkt"],
          "Combine VLANs, trunks, Rapid-PVST+, LACP and router-on-a-stick in one compact enterprise topology.",
          ["Create VLANs 10, 20 and 99.", "Build LACP Po1 over Gi0/0-1 between core/distribution.", "Use VLAN 99 as native VLAN on trunks.", "Tune STP roots by VLAN.", "Configure R1 router-on-a-stick for VLANs 10 and 20.", "Attach VPCS endpoints to user VLANs."],
          [R("R1-EDGE","12%","46%"),S("SW1-CORE","34%","28%"),S("SW2-DIST","60%","28%"),S("SW3-ACCESS","48%","66%"),P("PC-A","75%","66%"),P("PC-B","75%","82%")],
          [L("R1-EDGE","Gi0/0","SW1-CORE","Gi0/2"),L("SW1-CORE","Gi0/0","SW2-DIST","Gi0/0","LACP-LINK-1"),L("SW1-CORE","Gi0/1","SW2-DIST","Gi0/1","LACP-LINK-2"),L("SW1-CORE","Gi0/3","SW3-ACCESS","Gi0/0"),L("SW2-DIST","Gi0/3","SW3-ACCESS","Gi0/1"),L("SW3-ACCESS","Gi0/2","PC-A","eth0"),L("SW3-ACCESS","Gi0/3","PC-B","eth0")],
          [{"node":"SW1-CORE","command":"show etherchannel summary","assertions":[{"type":"etherchannel","port_channel":"Po1","protocol":"LACP","members":["Gi0/0","Gi0/1"]}]},{"node":"SW1-CORE","command":"show spanning-tree root","contains":["Vl10","Vl99"]},{"node":"SW2-DIST","command":"show spanning-tree root","contains":["Vl20"]},{"node":"R1-EDGE","command":"show running-config interface GigabitEthernet0/0.10","contains":["encapsulation dot1Q 10"]}], 75, "Advanced", "Network Access / IP Connectivity"),
    ]


_ARCHIVE = [
("PKT-01","ccna_troubleshooting1.pkt","review"),("PKT-02","CUSTOM1.pkt","review"),("PKT-03","EIGRP Troubleshooting Complete.pkt","legacy"),("PKT-04","EIGRP Troubleshooting.pkt","legacy"),("PKT-05","Frame Relay Troubleshooting.pkt","blocked"),("PKT-06","ICND1 RIP.pkt","legacy"),("PKT-07","ICND2 EIGRP.pkt","blocked"),("PKT-08","ICND2 OSPF.pkt","legacy"),("PKT-09","LAB.pkt","review"),("PKT-10","Multi-area OSPF Complete.pkt","legacy"),("PKT-11","Multi-area OSPF.pkt","legacy"),("PKT-12","OSPF Troubleshooting.pkt","migrated"),("PKT-13","EIGRP Troubleshooting.pkt (variant B)","legacy"),("PKT-14","Frame Relay.pkt","blocked"),("PKT-15","Scenario 1.pkt","review"),("PKT-16","Simple_Frame_Relay.pkt","blocked"),("PKT-17","SOHO.pkt","migrated"),("PKT-18","STP Load Balancing.pkt","migrated"),("PKT-19","STP.pkt","migrated"),("PKT-20","STP2.pkt","migrated"),("PKT-21","TASK05.pkt (variant A)","review"),("PKT-22","PPP Troubleshooting.pkt","blocked"),("PKT-23","STP3.pkt","migrated"),("PKT-24","TASK05.pkt (variant B)","review"),("PKT-25","Router on a stick.pkt","migrated"),("PKT-26","SVI.pkt","migrated"),("PKT-27","PhasedISPMigration.pkt","review"),("PKT-28","VLANs---SpanningTreeProtocol.pkt","migrated")]


def packet_tracer_archive():
    return [{"id": i, "name": n, "status": s} for i, n, s in _ARCHIVE]
