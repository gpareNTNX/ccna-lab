# Advanced Cisco and Data Center Labs

The core **CCNA 200-301 catalog remains 37 labs**. Advanced material is intentionally kept in separate non-numeric catalogs so the certification-focused path stays unchanged.

These scenarios are original implementations inspired by topics represented in the public EVE-NG Lab Library. No EVE-NG lab archive, workbook, Cisco image, or Nexus image is redistributed by this project.

## Advanced Cisco pack

The Advanced Cisco scenarios reuse the image families already supported by the application: **IOSv**, **IOSvL2**, and built-in **VPCS**.

| ID | Lab | Primary image family |
| --- | --- | --- |
| ADV-C01 | MSTP Region and Root Control | IOSvL2 |
| ADV-C02 | VTP Domain Operations | IOSvL2 |
| ADV-C03 | SPAN and RSPAN Monitoring | IOSvL2 + VPCS |
| ADV-C04 | Multi-Area OSPFv2 | IOSv |
| ADV-C05 | OSPF ABR Route Summarization | IOSv |
| ADV-C06 | Multi-Area OSPFv3 | IOSv |
| ADV-C07 | EIGRP Fundamentals | IOSv |
| ADV-C08 | eBGP Fundamentals | IOSv |

They appear in the existing Cisco Challenge workspace and remain isolated from labs 01-37.

## Bonus Nutanix / Data Center pack

The Bonus Nutanix workspace now contains three NX-OSv9K labs:

| ID | Lab | Primary image family |
| --- | --- | --- |
| NTNX-B01 | Cisco Nexus Best Practices for Nutanix | NX-OSv9K + VPCS |
| NTNX-B02 | Nexus vPC Operations and Failure Recovery | NX-OSv9K + VPCS |
| NTNX-B03 | VXLAN BGP EVPN Fundamentals for Nutanix Networks | NX-OSv9K + VPCS |

`NTNX-B02` adds operational vPC verification and controlled failure/recovery exercises. `NTNX-B03` introduces a compact two-VTEP fabric with an OSPF underlay, iBGP EVPN overlay, NVE interfaces, VLAN-to-VNI mapping, and VPCS workload attachment points.

## Resource guidance

NX-OSv9K is significantly heavier than IOSv/IOSvL2. The application currently requests 2 vCPU and 8 GB RAM per Nexus virtual switch in the Bonus Nutanix scenarios. A two-Nexus lab therefore requires substantially more EVE-NG capacity than a typical CCNA lab.

## Design principles

Every added lab follows the project's existing model:

1. generate a fresh EVE-NG topology;
2. cable the topology through the supported builder path;
3. present explicit student tasks;
4. expose integrated device consoles;
5. validate selected operational/configuration states live;
6. keep vendor images out of the repository.

The exercises are training material, not vendor production reference architectures. Validate real deployments against the relevant Cisco, Nutanix, and EVE-NG documentation for the software releases in use.
