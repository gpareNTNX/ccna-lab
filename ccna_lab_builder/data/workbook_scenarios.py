"""Original EVE-NG adaptations of the five labs in CCNA Practical Labs Workbook.

Expected states are derived from the workbook answer sections. Packet Tracer-only
GUI/server actions are intentionally left manual.
"""

TITLE = "CCNA Practical Labs Workbook"
AUTHOR = "Yasser Ramzy Auda"


def n(name, template, left, top):
    return {"name": name, "template": template, "left": left, "top": top}


def l(a, ai, b, bi):
    return {"a": a, "a_if": ai, "b": b, "b_if": bi}


def c(value, label=None):
    return {"type": "contains", "value": value, "label": label or value}


def ip(interface, address, label=None, up=True):
    a = {"type": "interface_ipv4", "interface": interface, "ip": address,
         "label": label or f"{interface} {address}"}
    if up:
        a.update(status="up", protocol="up")
    return a


def v(vid, name):
    return {"type": "vlan", "id": vid, "name": name, "label": f"VLAN {vid} {name}"}


def nbr(rid):
    return {"type": "ospf_neighbor", "router_id": rid, "state": "FULL",
            "label": f"OSPF neighbor {rid} FULL"}


def check(node, command, *assertions):
    return {"node": node, "command": command, "assertions": list(assertions)}


def src(lab, q, a):
    return {"title": TITLE, "author": AUTHOR, "workbook_lab": lab,
            "question_pages": q, "answer_pages": a}


def workbook_scenarios():
    lab1 = {
        "id": "33", "schema_version": 2,
        "name": "Workbook Lab 1 — Management & Services", "domain": "Mixed",
        "difficulty": "Medium", "minutes": 75,
        "objective": "Configure device management, DHCP, discovery and secure access.",
        "source": src(1, "2-4", "19-32"),
        "adaptation_notes": [
            "PC/server GUI actions remain manual; IOSv/IOSvL2 device state is validated.",
            "Use the standard lab access values shown by the application."
        ],
        "tasks": [
            "Use hostnames R1/R2/SW1/SW2/SW3 and domain cln.com.",
            "R1 Gi0/0 192.168.100.1/24; Gi0/1 200.200.200.1/24.",
            "Build DHCP NET192/NET200 with answer-key ranges, DNS 8.8.8.8 and option 150 200.200.200.100; R2 is a DHCP client.",
            "Enable CDP/LLDP globally on R1 but disable both on Gi0/1.",
            "VLAN1 management: SW1 .50, SW2 .51 in 192.168.100.0/24; SW3 200.200.200.50/24.",
            "Enable SSHv2, SSH-only VTY, timeout 60, retries 2; configure the R1 line/banner requirements."
        ],
        "topology": {
            "nodes": [n("SW1","viosl2","8%","30%"), n("SW2","viosl2","27%","50%"),
                      n("R1","vios","48%","50%"), n("SW3","viosl2","68%","50%"),
                      n("R2","vios","87%","30%")],
            "links": [l("SW1","Gi0/0","SW2","Gi0/0"), l("SW2","Gi0/1","R1","Gi0/0"),
                      l("R1","Gi0/1","SW3","Gi0/0"), l("SW3","Gi0/1","R2","Gi0/0")]
        },
        "checks": [
            check("R1","show ip interface brief",
                  ip("GigabitEthernet0/0","192.168.100.1"),
                  ip("GigabitEthernet0/1","200.200.200.1")),
            check("R1","show running-config | section ip dhcp",
                  c("ip dhcp pool NET192"), c("network 192.168.100.0 255.255.255.0"),
                  c("default-router 192.168.100.1"), c("dns-server 8.8.8.8"),
                  c("option 150 ip 200.200.200.100"),
                  c("ip dhcp excluded-address 192.168.100.1 192.168.100.199"),
                  c("ip dhcp excluded-address 192.168.100.221 192.168.100.255"),
                  c("ip dhcp pool NET200"), c("network 200.200.200.0 255.255.255.0"),
                  c("default-router 200.200.200.1"),
                  c("ip dhcp excluded-address 200.200.200.1 200.200.200.199"),
                  c("ip dhcp excluded-address 200.200.200.221 200.200.200.255")),
            check("R2","show running-config | section interface GigabitEthernet0/0",
                  c("ip address dhcp","R2 DHCP client")),
            check("R1","show running-config | include ^cdp run|^lldp run|no cdp enable|no lldp",
                  c("cdp run"), c("lldp run"), c("no cdp enable"),
                  c("no lldp receive"), c("no lldp transmit")),
            check("SW1","show ip interface brief",ip("Vlan1","192.168.100.50",up=False)),
            check("SW2","show ip interface brief",ip("Vlan1","192.168.100.51",up=False)),
            check("SW3","show ip interface brief",ip("Vlan1","200.200.200.50",up=False)),
            check("R1","show ip ssh",
                  {"type":"ssh_enabled","label":"SSHv2 enabled"},
                  c("Authentication retries: 2"), c("Authentication timeout: 60")),
            check("R1","show running-config | section line vty",
                  c("login local"), c("transport input ssh"), c("exec-timeout 0 0"),
                  c("logging synchronous"), c("history size 256")),
            check("R1","show running-config | include ^banner motd",c("This is R1"))
        ]
    }

    lab2 = {
        "id": "34", "schema_version": 2,
        "name": "Workbook Lab 2 — Dual Stack & OSPF", "domain": "IP Connectivity",
        "difficulty": "Hard", "minutes": 75,
        "objective": "Configure dual stack, OSPFv2 area 51, IPv6 static routes and NTP.",
        "source": src(2, "5-6", "33-40"),
        "adaptation_notes": ["PC/server addressing and the TFTP copy remain manual."],
        "tasks": [
            "IPv4: R1 10.0.0.1/8 + 11.0.0.1/8; R2 12.0.0.2/8 + 11.0.0.2/8; R3 10.0.0.3/8.",
            "IPv6: R1 2001:1:1:1::1 and 2001:2:2:2::1; R2 2001:3:3:3::2 and 2001:2:2:2::2; R3 2001:1:1:1::3 (/64).",
            "OSPF process 1 area 51, router IDs 1.1.1.1 / 2.2.2.2 / 3.3.3.3.",
            "Configure the answer-key IPv6 static routes and NTP 12.0.0.100."
        ],
        "topology": {
            "nodes": [n("R3","vios","12%","68%"), n("R1","vios","42%","32%"),
                      n("R2","vios","75%","32%")],
            "links": [l("R1","Gi0/0","R3","Gi0/0"), l("R1","Gi0/1","R2","Gi0/1")]
        },
        "checks": [
            check("R1","show ip interface brief",ip("GigabitEthernet0/0","10.0.0.1"),
                  ip("GigabitEthernet0/1","11.0.0.1")),
            check("R2","show ip interface brief",ip("GigabitEthernet0/0","12.0.0.2",up=False),
                  ip("GigabitEthernet0/1","11.0.0.2")),
            check("R3","show ip interface brief",ip("GigabitEthernet0/0","10.0.0.3")),
            check("R1","show ipv6 interface brief",c("2001:1:1:1::1"),c("2001:2:2:2::1")),
            check("R2","show ipv6 interface brief",c("2001:3:3:3::2"),c("2001:2:2:2::2")),
            check("R3","show ipv6 interface brief",c("2001:1:1:1::3")),
            check("R1","show running-config | section router ospf 1",
                  c("router-id 1.1.1.1"),c("network 10.0.0.0 0.255.255.255 area 51"),
                  c("network 11.0.0.0 0.255.255.255 area 51")),
            check("R1","show ip ospf neighbor",nbr("2.2.2.2"),nbr("3.3.3.3")),
            check("R1","show running-config | include ^ipv6 route",
                  c("ipv6 route 2001:3:3:3::/64 2001:2:2:2::2")),
            check("R2","show running-config | include ^ipv6 route",
                  c("ipv6 route 2001:1:1:1::/64 2001:2:2:2::1")),
            check("R3","show running-config | include ^ipv6 route",
                  c("ipv6 route ::/0 2001:1:1:1::1")),
            check("R1","show running-config | include ^ntp server",c("ntp server 12.0.0.100")),
            check("R2","show running-config | include ^ntp server",c("ntp server 12.0.0.100")),
            check("R3","show running-config | include ^ntp server",c("ntp server 12.0.0.100"))
        ]
    }

    lab3 = {
        "id": "35", "schema_version": 2,
        "name": "Workbook Lab 3 — VLAN, Trunk & Router-on-a-Stick",
        "domain": "Network Access", "difficulty": "Medium", "minutes": 65,
        "objective": "Build the answer-key VLAN, trunk, router-on-a-stick and DHCP design.",
        "source": src(3, "7-8", "41-45"),
        "adaptation_notes": ["FastEthernet access ports are mapped to IOSvL2 GigabitEthernet ports."],
        "tasks": [
            "Create VLAN 2 Sales, VLAN 3 IT and VLAN 999 Unused on SW1/SW2.",
            "Trunk SW1-SW2 and SW1-R1.",
            "R1 Gi0/2.2 2.0.0.1/8; Gi0/2.3 3.0.0.1/8.",
            "Build DHCP NET2/NET3 with the answer-key exclusions."
        ],
        "topology": {
            "nodes": [n("R1","vios","48%","12%"), n("SW1","viosl2","28%","58%"),
                      n("SW2","viosl2","68%","58%")],
            "links": [l("SW1","Gi0/0","SW2","Gi0/0"),l("SW1","Gi0/1","R1","Gi0/2")]
        },
        "checks": [
            check("SW1","show vlan brief",v(2,"Sales"),v(3,"IT"),v(999,"Unused")),
            check("SW2","show vlan brief",v(2,"Sales"),v(3,"IT"),v(999,"Unused")),
            check("SW1","show interfaces trunk",
                  {"type":"trunk","interface":"Gi0/0","label":"SW1-SW2 trunk"},
                  {"type":"trunk","interface":"Gi0/1","label":"SW1-R1 trunk"}),
            check("R1","show ip interface brief",
                  ip("GigabitEthernet0/2.2","2.0.0.1"),ip("GigabitEthernet0/2.3","3.0.0.1")),
            check("R1","show running-config | section ip dhcp",
                  c("ip dhcp pool NET2"),c("network 2.0.0.0 255.0.0.0"),
                  c("default-router 2.0.0.1"),c("ip dhcp excluded-address 2.0.0.1 2.0.0.99"),
                  c("ip dhcp excluded-address 2.0.0.201 2.255.255.255"),
                  c("ip dhcp pool NET3"),c("network 3.0.0.0 255.0.0.0"),
                  c("default-router 3.0.0.1"),c("ip dhcp excluded-address 3.0.0.1 3.0.0.99"),
                  c("ip dhcp excluded-address 3.0.0.201 3.255.255.255"))
        ]
    }

    lab4 = {
        "id": "36", "schema_version": 2,
        "name": "Workbook Lab 4 — Enterprise Integration", "domain": "Mixed",
        "difficulty": "Hard", "minutes": 120,
        "objective": "Integrate VLANs, LACP, DHCP, OSPF, static NAT and management services.",
        "source": src(4, "9-12", "46-56"),
        "adaptation_notes": [
            "The question and answer disagree on R1 Gi0/1; validation follows the answer: 10.0.0.1/8.",
            "The answer contains a hostname typo RO; this adaptation uses R0.",
            "The answer FTP ACL has a broad permit before a later deny, so that flawed order is not required.",
            "Use standard lab access values shown by the application; PC/server, FTP/TFTP actions remain manual.",
            "The workbook SNMP read-write value is mapped to training value CCNA-RW."
        ],
        "tasks": [
            "VLAN 2 Sales, VLAN 3 IT, VLAN 200 Internet, VLAN 999 Unused.",
            "Po5 LACP: SW1 active, SW2 passive, trunk.",
            "R1 ROAS: 20.0.0.1/8, 30.0.0.1/8, 200.200.200.1/24; R1-R2 10.0.0.1/8 to 10.0.0.2/8.",
            "R0 DHCP client + Loopback100 100.100.100.100/8; configure answer-key DHCP pools.",
            "OSPF process 1 area 51; static NAT 11.0.0.200 -> 10.0.0.2; NTP/Syslog/SNMP management."
        ],
        "topology": {
            "nodes": [n("R0","vios","7%","18%"), n("SW1","viosl2","18%","58%"),
                      n("SW2","viosl2","38%","58%"), n("R1","vios","53%","35%"),
                      n("R2","vios","70%","35%"), n("SW3","viosl2","88%","58%")],
            "links": [l("SW1","Gi0/0","SW2","Gi0/0"),l("SW1","Gi0/1","SW2","Gi0/1"),
                      l("R0","Gi0/0","SW2","Gi0/3"),l("SW2","Gi0/2","R1","Gi0/0"),
                      l("R1","Gi0/1","R2","Gi0/0"),l("R2","Gi0/1","SW3","Gi0/0")]
        },
        "checks": [
            check("SW1","show vlan brief",v(2,"Sales"),v(3,"IT"),v(200,"Internet"),v(999,"Unused")),
            check("SW1","show etherchannel summary",
                  {"type":"etherchannel","port_channel":"Po5","protocol":"LACP",
                   "members":["Gi0/0","Gi0/1"],"label":"SW1 Po5 LACP"}),
            check("SW2","show etherchannel summary",
                  {"type":"etherchannel","port_channel":"Po5","protocol":"LACP",
                   "members":["Gi0/0","Gi0/1"],"label":"SW2 Po5 LACP"}),
            check("R1","show ip interface brief",
                  ip("GigabitEthernet0/0.2","20.0.0.1"),ip("GigabitEthernet0/0.3","30.0.0.1"),
                  ip("GigabitEthernet0/0.200","200.200.200.1"),ip("GigabitEthernet0/1","10.0.0.1")),
            check("R0","show running-config | include ip address dhcp|100.100.100.100",
                  c("ip address dhcp"),c("ip address 100.100.100.100 255.0.0.0")),
            check("R1","show ip ospf neighbor",nbr("2.2.2.2"),nbr("0.0.0.200")),
            check("R2","show running-config | include ^ip nat|ip nat inside|ip nat outside",
                  c("ip nat inside source static 11.0.0.200 10.0.0.2"),
                  c("ip nat inside"),c("ip nat outside")),
            check("R2","show running-config | include ^ntp server|^logging|^service timestamps|^snmp",
                  c("ntp server 11.0.0.200"),c("logging host 11.0.0.200"),
                  c("logging trap debugging"),
                  {"type":"regex","pattern":"service timestamps log datetime.*msec","label":"Log timestamps"},
                  {"type":"regex","pattern":"snmp-server community CCNA-RW RW","label":"SNMP RW training value"})
        ]
    }

    lab5 = {
        "id": "37", "schema_version": 2,
        "name": "Workbook Lab 5 — Advanced Enterprise Mega Lab", "domain": "Mixed",
        "difficulty": "Expert", "minutes": 180,
        "objective": "Practice multilayer switching, DHCP relay, OSPF, L2 security, HSRP and OSPFv3.",
        "source": src(5, "13-18", "57-72"),
        "adaptation_notes": [
            "Multilayer-switch Gi1/0/x ports are mapped to IOSvL2 Gi0/x ports.",
            "Use standard lab access values shown by the application.",
            "The question shows management/controller host .50 while the answer uses .150; validation follows 199.199.199.150.",
            "Network Controller GUI, evaluation-license and TFTP-copy tasks remain manual.",
            "The workbook SNMP read-write value is mapped to training value CCNA-RW."
        ],
        "tasks": [
            "VLAN 2 Sales, VLAN 3 IT, VLAN 999 Unused; Po10 LACP active/passive trunk excluding VLAN999.",
            "MLS2 L3 SVIs/routed uplink and answer-key routed links on R1/R2/R3/R4.",
            "R2 DHCP NET2 + MLS2 helper; OSPFv2 process 1 area 51 with passive behavior and R1 priority 0.",
            "Configure PortFast/BPDU Guard/no-CDP/sticky one-MAC port-security.",
            "HSRP group1 VIP 199.199.199.50: R3 Active priority120/preempt/track; R4 Standby.",
            "NTP/Syslog/SNMP, R3 VTY ACL answer host .150, IPv6 and OSPFv3 area0."
        ],
        "topology": {
            "nodes": [n("MLS1","viosl2","5%","42%"),n("MLS2","viosl2","25%","42%"),
                      n("R1","vios","18%","10%"),n("R2","vios","49%","42%"),
                      n("R3","vios","64%","12%"),n("R4","vios","69%","70%"),
                      n("SW1","viosl2","88%","42%")],
            "links": [l("MLS1","Gi0/6","MLS2","Gi0/6"),l("MLS1","Gi0/7","MLS2","Gi0/7"),
                      l("R1","Gi0/0","MLS1","Gi0/0"),l("MLS2","Gi0/2","R2","Gi0/0"),
                      l("R1","Gi0/1","R3","Gi0/1"),l("R2","Gi0/1","R3","Gi0/2"),
                      l("R2","Gi0/2","R4","Gi0/1"),l("R3","Gi0/0","SW1","Gi0/0"),
                      l("R4","Gi0/0","SW1","Gi0/1")]
        },
        "checks": [
            check("MLS1","show vlan brief",v(2,"Sales"),v(3,"IT"),v(999,"Unused")),
            check("MLS2","show vlan brief",v(2,"Sales"),v(3,"IT"),v(999,"Unused")),
            check("MLS1","show etherchannel summary",
                  {"type":"etherchannel","port_channel":"Po10","protocol":"LACP",
                   "members":["Gi0/6","Gi0/7"],"label":"MLS1 Po10 LACP"}),
            check("MLS2","show ip interface brief",ip("Vlan1","1.0.0.2",up=False),
                  ip("Vlan2","202.202.202.1",up=False),ip("Vlan3","203.203.203.1",up=False),
                  ip("GigabitEthernet0/2","192.168.100.10")),
            check("R2","show running-config | section ip dhcp",
                  c("ip dhcp pool NET2"),c("network 202.202.202.0 255.255.255.0"),
                  c("default-router 202.202.202.1"),c("dns-server 199.199.199.2"),
                  c("ip dhcp excluded-address 202.202.202.1 202.202.202.100"),
                  c("ip dhcp excluded-address 202.202.202.121 202.202.202.255")),
            check("MLS2","show running-config | section interface Vlan2",
                  c("ip helper-address 192.168.100.9")),
            check("R2","show ip ospf neighbor",nbr("3.3.3.3"),nbr("4.4.4.4"),nbr("0.0.0.2")),
            check("R3","show running-config | section router ospf 1",
                  c("router-id 3.3.3.3"),c("passive-interface default"),
                  c("no passive-interface GigabitEthernet0/0"),
                  c("no passive-interface GigabitEthernet0/1"),
                  c("no passive-interface GigabitEthernet0/2")),
            check("R1","show running-config | section interface GigabitEthernet0/1",
                  c("ip ospf priority 0")),
            check("MLS1","show running-config | section interface GigabitEthernet0/0",
                  c("spanning-tree portfast"),c("spanning-tree bpduguard enable"),c("no cdp enable"),
                  c("switchport port-security maximum 1"),
                  c("switchport port-security mac-address sticky"),
                  c("switchport port-security violation shutdown")),
            check("R3","show standby brief",
                  {"type":"hsrp","state":"Active","virtual_ip":"199.199.199.50","label":"R3 HSRP Active"}),
            check("R4","show standby brief",
                  {"type":"hsrp","state":"Standby","virtual_ip":"199.199.199.50","label":"R4 HSRP Standby"}),
            check("R3","show running-config | section interface GigabitEthernet0/0",
                  c("standby 1 priority 120"),c("standby 1 preempt"),
                  c("standby 1 track GigabitEthernet0/1")),
            check("R2","show running-config | include ^ntp server|^logging|^service timestamps|^snmp",
                  c("ntp server 199.199.199.2"),c("logging host 199.199.199.2"),
                  c("logging trap debugging"),
                  {"type":"regex","pattern":"snmp-server community CCNA-RW RW","label":"SNMP RW training value"}),
            check("R3","show access-lists 1",c("199.199.199.2"),c("199.199.199.150")),
            check("R2","show ipv6 interface brief",c("2001:32:32:32:"),c("2001:24:24:24:")),
            check("R3","show ipv6 interface brief",c("2001:34:34:34::3"),c("2001:32:32:32::3")),
            check("R4","show ipv6 interface brief",c("2001:34:34:34::4"),c("2001:24:24:24::4")),
            check("R2","show ipv6 ospf neighbor",c("3.3.3.3"),c("4.4.4.4"))
        ]
    }

    return [lab1, lab2, lab3, lab4, lab5]
