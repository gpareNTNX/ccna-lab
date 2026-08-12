# Integration with an existing EVE-NG server

## Scope

This project is an **EVE-NG client/integration tool**, not an EVE-NG deployment tool.

EVE-NG must already be installed, licensed/configured as appropriate, reachable, and operational before you use CCNA EVE Lab Builder. The application does not create the EVE-NG VM, install EVE-NG Community/Pro, configure the hypervisor, or enable nested virtualization.

The application connects to the existing server using:

1. the EVE-NG API for lab lifecycle and inventory;
2. SSH/SCP for Cisco image import and console tunneling.

## Cisco image import

When you explicitly select an IOSv/IOSvL2 image, the application can upload that image **to the existing EVE-NG server** under:

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

The QEMU disk is placed as:

```text
virtioa.qcow2
```

After image import, the application runs on the existing server:

```bash
/opt/unetlab/wrappers/unl_wrapper -a fixpermissions
```

This operation imports lab images only; it does not install or redeploy EVE-NG itself.

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

The topology is created inside the existing EVE-NG environment.

## Stable API operations used

The application uses EVE-NG operations for:

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

- **off**: node creation is stable; cable in the existing EVE-NG UI.
- **on**: V4 attempts the commonly used interface assignment request and verifies interface names first.

If the experimental method fails, disable it and cable the topology manually in EVE-NG.
