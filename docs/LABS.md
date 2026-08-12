# CCNA training labs

V4 ships with 20 scenarios:

| # | Lab | Domain |
|---|---|---|
| 01 | Initial Configuration | Network Fundamentals |
| 02 | IPv4 Addressing | Network Fundamentals |
| 03 | IPv6 | Network Fundamentals |
| 04 | VLAN | Network Access |
| 05 | 802.1Q Trunking | Network Access |
| 06 | EtherChannel | Network Access |
| 07 | STP / RSTP | Network Access |
| 08 | Inter-VLAN Routing | IP Connectivity |
| 09 | Static Routing | IP Connectivity |
| 10 | OSPF | IP Connectivity |
| 11 | DHCP | IP Services |
| 12 | NAT / PAT | IP Services |
| 13 | ACL | Security Fundamentals |
| 14 | Port Security | Security Fundamentals |
| 15 | DHCP Snooping | Security Fundamentals |
| 16 | Dynamic ARP Inspection | Security Fundamentals |
| 17 | SSH Management | Security Fundamentals |
| 18 | Network Services | IP Services |
| 19 | Troubleshooting | Mixed |
| 20 | Practice Exam | Mixed |

Each entry in `ccna_lab_builder/data/scenarios.json` contains:

- objective
- difficulty
- suggested duration
- tasks
- validation commands
- expected output tokens

This makes the lab catalog data-driven: adding a lab does not require changing the GUI.
