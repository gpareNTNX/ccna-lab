# EVE-NG integration

## Image directories

V4 uploads QEMU images under:

```text
/opt/unetlab/addons/qemu/
```

IOSv folders start with:

```text
vios-
```

IOSvL2 folders start with:

```text
viosl2-
```

The QEMU disk is installed as:

```text
virtioa.qcow2
```

The installer then runs:

```bash
/opt/unetlab/wrappers/unl_wrapper -a fixpermissions
```

## Master topology

```text
                           R5-ISP
                              |
R1-EDGE ---- R2-HQ ---- R3-HQ
   |            |          |
   |         SW1-CORE === SW2-DIST
   |            |          |
   |        SW3-ACCESS  SW4-BRANCH
   |                       |
   +------------------- R4-BRANCH
```

The exact drawing in EVE-NG is positioned by percentages.

## Stable API operations used

V4 uses documented API operations for:

- authentication
- create lab
- create node
- create network
- list nodes
- inspect node interfaces
- inspect topology
- start nodes
- stop nodes
- wipe nodes
- export startup configurations

## Cabling compatibility mode

The public EVE-NG API documentation describes how to inspect interfaces and topology, but does not clearly document the interface-to-network write request.

Therefore:

- **off**: node creation is stable; cable in the EVE UI.
- **on**: V4 attempts the commonly used interface assignment request and verifies interface names first.

If the experimental method fails, disable it and cable the topology manually.
