# CCNA 200-301 EVE-NG Lab Builder

A desktop GUI for building, practicing, and validating **CCNA 200-301** labs on an **existing EVE-NG server**, using Cisco IOSv and IOSvL2 images that you provide legally.

> **Deployment scope:** EVE-NG is assumed to be already deployed and operational. This repository does **not** install, provision, package, or deploy EVE-NG. The CCNA EVE Lab Builder application is intended to be run directly from source on Windows, macOS, or Linux.

> **Cisco images are not included.** You must provide your own legally obtained IOSv / IOSvL2 images. Never commit Cisco images to this repository.

## Architecture at a glance

```text
Windows / macOS / Linux workstation
        |
        |  CCNA EVE Lab Builder
        |  EVE Web/API + SSH
        |  live IOS console validation
        v
Existing EVE-NG server
        |
        +-- IOSv
        +-- IOSvL2
        +-- generated CCNA labs
        +-- per-scenario EVE runtime
```

## Current feature set

- Connects to an already deployed EVE-NG server through **SSH + EVE Web/API**.
- Uses separate SSH and API credentials.
- Imports user-supplied IOSv / IOSvL2 images into EVE-NG.
- Scans the EVE-NG image inventory.
- Creates a reusable 9-device master topology.
- Creates **fresh scenario-specific labs**.
- Supports **scenario-specific topologies** for newer labs instead of always creating the full master topology.
- Optional experimental API cabling compatibility mode.
- Start / stop / wipe node controls.
- **37 training labs** across Network Fundamentals, Network Access, IP Connectivity, IP Services, Security, troubleshooting, and integrated practical labs.
- Legacy and **Scenario V2** lab schemas are supported together.
- **Live validation** through Cisco console sessions reached through the EVE-NG server.
- Prompt-aware IOS command capture instead of fixed sleep timers.
- Automatic IOS boot wait, initial-dialog handling, login, and `enable` handling.
- Structured validation assertions for interfaces, VLANs, trunks, EtherChannel, routes, OSPF neighbors, HSRP, CDP, SSH, regex checks, positive/negative text checks, and more.
- Detailed validation reports with expected, matched, missing, observed output, target identity, and suggested remediation commands.
- GitHub Actions CI and unit tests.

## Lab catalog

The application currently contains **37 labs**.

### Labs 01–20 — Core CCNA scenarios

1. Initial Configuration
2. IPv4 Addressing
3. IPv6 Addressing
4. VLANs
5. 802.1Q Trunking
6. EtherChannel
7. STP / RSTP
8. Inter-VLAN Routing
9. Static Routing
10. OSPF
11. DHCP
12. NAT / PAT
13. ACLs
14. Port Security
15. DHCP Snooping
16. Dynamic ARP Inspection
17. SSH Management
18. Network Services
19. Troubleshooting
20. Practice Exam

### Labs 21–32 — Scenario V2 labs

21. Interface Operations
22. CDP and LLDP Discovery
23. NTP Configuration
24. Syslog Management
25. HSRP First-Hop Redundancy
26. SNMP Operations
27. DNS Client Configuration
28. DTP and Trunk Negotiation
29. OSPF Multi-Router Deep Dive
30. VLAN Multi-Segment
31. ACL Verification Lab
32. CCNA Mega Lab V2

Scenario V2 labs can define their own nodes, links, tasks, difficulty, estimated time, and structured validation assertions.

### Labs 33–37 — Practical workbook adaptations

33. Workbook Practical Lab 1 — Management & Services
34. Workbook Practical Lab 2 — Dual Stack & OSPF
35. Workbook Practical Lab 3 — VLAN, Trunk & Router-on-a-Stick
36. Workbook Practical Lab 4 — Enterprise Integration
37. Workbook Practical Lab 5 — Advanced Enterprise Mega Lab

These labs are EVE-NG adaptations of the user-supplied **CCNA Practical Labs Workbook** by Yasser Ramzy Auda. Expected states are derived from the workbook's answer sections. Packet Tracer-specific GUI tasks such as PC/server configuration, controller GUI operations, licensing steps, and some TFTP interactions are adapted or left as manual tasks when they cannot be validated meaningfully with IOSv/IOSvL2 alone.

Where the workbook question and answer sections disagree, the scenario documents the adaptation and uses an explicit expected state rather than silently guessing.

## Prerequisite: existing EVE-NG

Before running this application, you should already have:

- an operational EVE-NG Community or Pro server;
- network reachability from the workstation to EVE-NG;
- SSH access to the EVE-NG server;
- an EVE-NG account usable through the Web/API;
- legal IOSv and IOSvL2 images if you want the application to import them;
- Python with Tkinter available on the workstation running the application.

EVE-NG installation, hypervisor configuration, VM sizing, nested virtualization, upgrades, and backups are outside this project's deployment scope.

## Standard IOS lab credentials

The training labs use standard credentials so the live Validator can authenticate predictably.

```text
IOS username:      admin
IOS password:      CCNAadmin!
Enable secret:     CCNAenable!
```

These are **training-only credentials**. Do not reuse them on production equipment or real networks.

A typical lab configuration is:

```cisco
username admin privilege 15 secret CCNAadmin!
enable secret CCNAenable!

line console 0
 login local

line vty 0 4
 login local
 transport input ssh
```

The Validator can handle:

```text
Username:
Password:
Router>
enable
Password:
Router#
```

If the device is already at privileged EXEC (`R1#`), no login or enable sequence is required.

## Quick start — macOS

### Recommended helper script

```bash
git clone https://github.com/gpareNTNX/ccna-lab.git
cd ccna-lab
./scripts/run_mac.sh
```

If Homebrew Python reports that Tkinter is unavailable, install the matching `python-tk` package for your Python version. For example, with Homebrew Python 3.14:

```bash
brew install python-tk@3.14
```

### Manual source execution

```bash
git clone https://github.com/gpareNTNX/ccna-lab.git
cd ccna-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ccna_lab_builder.app
```

## Quick start — Linux

```bash
git clone https://github.com/gpareNTNX/ccna-lab.git
cd ccna-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ccna_lab_builder.app
```

A working Python/Tk installation is required when running from source.

## Quick start — Windows

Windows 10/11 x64 is supported. The application is run directly from source.

### PowerShell

Install **Python 3.10+** for Windows, then open PowerShell:

```powershell
git clone https://github.com/gpareNTNX/ccna-lab.git
cd ccna-lab

py -3 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ccna_lab_builder.app
```

If `py` is not available but `python` is in your PATH:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ccna_lab_builder.app
```

### Command Prompt

```bat
git clone https://github.com/gpareNTNX/ccna-lab.git
cd ccna-lab
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ccna_lab_builder.app
```

## Connecting the application to EVE-NG

The application needs two sets of EVE-NG-side credentials:

- **SSH credentials** for the EVE-NG Linux server; and
- **EVE Web/API credentials** for lab/node operations.

They do not need to be the same account.

Typical workflow:

1. Enter EVE-NG host/IP.
2. Enter SSH username/password.
3. Enter EVE Web/API username/password.
4. Run the connection test.
5. Scan/import IOSv and IOSvL2 images.
6. Select or create a training scenario.

## IOSv / IOSvL2 image handling

The application can help import user-provided legal Cisco images into the existing EVE-NG server.

Typical EVE-NG image layout uses:

```text
/opt/unetlab/addons/qemu/vios-*/virtioa.qcow2
/opt/unetlab/addons/qemu/viosl2-*/virtioa.qcow2
```

The application never bundles Cisco image files.

## Recommended training workflow

1. Start with your already deployed EVE-NG server.
2. Launch CCNA EVE Lab Builder on Windows, macOS, or Linux.
3. Connect SSH + EVE Web/API.
4. Import or scan IOSv and IOSvL2.
5. Select a training lab.
6. Review the scenario objective, tasks, topology, and lab credentials.
7. Create a fresh scenario lab.
8. Enable experimental API cabling if you want the application to attempt automatic link creation.
9. Start the nodes or let validation start the required node when appropriate.
10. Configure the Cisco devices yourself.
11. Run **VALIDATE LIVE**.
12. Review PASS/FAIL checks, observed IOS output, and suggested remediation.
13. Correct the configuration and validate again.

## Live validation architecture

Live validation does more than compare text from a generic Telnet port.

When SSH access to EVE-NG is available, the Validator attempts to identify the **exact EVE runtime** for the selected lab/node using:

```text
lab path
  + lab UUID
  + node ID
  + /opt/unetlab/tmp/<POD>/<LAB_UUID>/<NODE_ID>
```

It then resolves the QEMU console backend associated with that runtime. The project includes compatibility parsing for EVE `qemu_wrapper` arguments and EVE POD/node console behavior.

The Validator intentionally refuses to trust an EVE API console port merely because the TCP port is listening when SSH runtime verification is available. This prevents validation from accidentally reading a different node or a different EVE POD.

A validation report can include target diagnostics similar to:

```text
[Validator target]
lab=/CCNA-200-301/CCNA-01-INITIAL-CONFIGURATION.unl
lab_uuid=<uuid>
node_id=1
uuid=<node-uuid>
prompt=R1-EDGE#
backend=<verified runtime console>
```

### IOS boot and prompt handling

The Validator:

- waits for IOS to boot instead of assuming that QEMU availability means IOS is ready;
- sends Return when required;
- handles the initial configuration dialog;
- recognizes IOS user EXEC, privileged EXEC, and configuration prompts;
- authenticates with the documented training credentials when prompted;
- enters `enable` automatically when necessary;
- waits for the IOS prompt after each command instead of relying on a fixed sleep timer;
- removes command echo, prompts, ANSI sequences, Telnet negotiation bytes, and terminal artifacts before evaluating output.

A local `telnet` executable on macOS or Windows is **not required for the application's live Validator** because the application reaches console backends through the EVE-NG connection logic.

## Validation engine

Legacy checks remain supported:

```json
{
  "node": "R1",
  "command": "show ip ssh",
  "contains": ["SSH Enabled"]
}
```

Scenario V2 supports structured assertions, for example:

```json
{
  "node": "R1",
  "command": "show ip interface brief",
  "assertions": [
    {
      "type": "interface_ipv4",
      "interface": "GigabitEthernet0/0",
      "ip": "10.0.12.1",
      "status": "up",
      "protocol": "up"
    }
  ]
}
```

Current structured assertion families include:

- `contains`
- `not_contains`
- `regex`
- `interface_ipv4`
- `vlan`
- `ospf_neighbor`
- `route`
- `trunk`
- `etherchannel`
- `hsrp`
- `cdp_neighbor`
- `ssh_enabled`

This allows a lab to validate operational state rather than simply finding one word somewhere in command output.

## Validation report

A typical report shows:

```text
Score: 100%

PASS | R1-EDGE | show running-config | include hostname
  Expected: hostname R1-EDGE
  Matched: hostname R1-EDGE
  Observed output:
    hostname R1-EDGE

PASS | R1-EDGE | show ip ssh
  Expected: SSH Enabled
  Matched: SSH Enabled
  Observed output:
    SSH Enabled - version 2.0
```

For failures, the report can include:

```text
Missing: ...
Suggested commands:
  ...
```

Suggested commands are remediation guidance. They should still be reviewed before being pasted into a device.

## Scenario architecture

The catalog currently combines three generations of scenario data:

```text
ccna_lab_builder/data/scenarios.json
    -> Labs 01-20 / legacy-compatible scenarios

ccna_lab_builder/data/scenarios_v2.json
    -> Labs 21-32 / Scenario V2

ccna_lab_builder/data/workbook_scenarios.py
    -> Labs 33-37 / practical workbook adaptations
```

Scenario V2 can describe a lab-specific topology:

```json
{
  "topology": {
    "nodes": [
      {"name": "R1", "template": "vios"},
      {"name": "R2", "template": "vios"}
    ],
    "links": [
      {"a": "R1", "a_if": "Gi0/0", "b": "R2", "b_if": "Gi0/0"}
    ]
  }
}
```

This avoids deploying the complete master topology when a lab only needs two or three devices.

## Experimental automatic cabling

The public EVE-NG API clearly documents many lab/node/network operations, but automated interface-to-network assignment can vary across EVE-NG editions and versions.

Automatic cabling therefore remains behind the explicit **experimental compatibility option**.

Without it, the application still creates the scenario's nodes and layout; links can be completed manually in the existing EVE-NG UI.

## Project layout

```text
ccna-lab/
├── ccna_lab_builder/
│   ├── app.py
│   ├── cli.py
│   ├── core/
│   │   ├── builder.py
│   │   ├── console_auth.py
│   │   ├── eve_api.py
│   │   ├── eve_wrapper_console.py
│   │   ├── live_validation.py
│   │   ├── scenarios.py
│   │   ├── ssh.py
│   │   └── validator.py
│   ├── data/
│   │   ├── scenarios.json
│   │   ├── scenarios_v2.json
│   │   └── workbook_scenarios.py
│   └── gui/
├── docs/
├── tests/
├── scripts/
│   ├── run_mac.sh
│   └── run_linux.sh
├── .github/
├── launcher.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Known limitations

- Automated cabling remains experimental and can depend on the EVE-NG edition/version.
- Some practical workbook tasks require PCs, servers, controllers, TFTP/FTP services, or Packet Tracer-specific GUI behavior and therefore remain manual or are represented by network-device-side checks.
- A fresh scenario lab starts from unconfigured IOS nodes unless the scenario explicitly provides another starting state.
- IOSv / IOSvL2 feature support depends on the images supplied by the user.
- The Validator requires working access to the selected EVE-NG lab and its IOS console runtime.
- Suggested remediation is not a substitute for understanding the requested CCNA task.

## Troubleshooting quick checks

If validation reports the wrong hostname/configuration, check the `[Validator target]` block and confirm the exact lab path, lab UUID, node ID, node UUID, IOS prompt, and backend.

If validation cannot find a console backend, verify:

- the node exists in the selected scenario lab;
- EVE-NG SSH is working;
- the node can start normally in EVE-NG;
- QEMU/IOS has enough time to boot;
- the application can identify the node runtime under `/opt/unetlab/tmp/`.

If authentication reaches `Router>` but not `Router#`, verify that the standard lab username/password and enable secret are configured.

See [Troubleshooting](docs/TROUBLESHOOTING.md) for more detail.

## Documentation

- [Application installation](docs/INSTALLATION.md)
- [Existing EVE-NG integration](docs/EVE-NG.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Training labs](docs/LABS.md)
- [Validation](docs/VALIDATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [GitHub publishing](docs/GITHUB.md)
- [Contributing](CONTRIBUTING.md)

## Building and testing from source

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run unit tests:

```bash
python -m unittest discover -s tests -v
```

Run Ruff:

```bash
ruff check ccna_lab_builder tests
```

## Legal and attribution

This project is not affiliated with Cisco or EVE-NG. Cisco, IOS, IOSv, EVE-NG, and related marks belong to their respective owners.

No vendor images are distributed with this repository.

Labs 33–37 are original EVE-NG adaptations based on a user-supplied **CCNA Practical Labs Workbook** credited in that document to **Yasser Ramzy Auda, CCIE #45694, CCSI #34215**. The project uses the workbook as a source for technical exercise objectives and expected validation states; it does not bundle the workbook itself.

MIT licensed.