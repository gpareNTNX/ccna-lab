# CCNA 200-301 EVE-NG Lab Builder

A desktop GUI for building and practicing **CCNA 200-301** labs on an **existing EVE-NG server**, using Cisco IOSv and IOSvL2 images that you provide legally.

> **Deployment scope:** EVE-NG is assumed to be already deployed and operational. This repository does **not** install, provision, package, or deploy EVE-NG. The Windows and macOS packages install only the **CCNA EVE Lab Builder desktop application**.

## Architecture at a glance

```text
Windows / macOS workstation
        |
        |  CCNA EVE Lab Builder
        |  HTTPS/HTTP API + SSH
        v
Existing EVE-NG server
        |
        +-- IOSv
        +-- IOSvL2
        +-- generated CCNA labs
```

## V4 highlights

- Connects to an already deployed EVE-NG server through SSH + API
- IOSv / IOSvL2 image import into that existing EVE-NG server
- Image inventory scan
- 9-device master topology
- Optional compatibility backend for automated cabling
- 20 CCNA practice scenarios
- Fresh scenario-lab creation
- Start / stop / wipe controls
- **Live validation** through Cisco console sessions tunneled over EVE-NG SSH
- GitHub Actions CI
- Unit tests
- Windows and macOS desktop application packaging

> Cisco images are **not included** and must never be committed to this repository.

## Prerequisite: existing EVE-NG

Before installing this application, you should already have:

- an operational EVE-NG Community or Pro server;
- network reachability from the workstation to EVE-NG;
- SSH access to EVE-NG;
- an EVE-NG account usable through the API;
- legal IOSv and IOSvL2 images if you want the application to import them.

EVE-NG installation, hypervisor configuration, VM sizing, nested virtualization, upgrades and backups are outside this project's deployment scope.

## Quick start

### From source on macOS / Linux

```bash
git clone https://github.com/gpareNTNX/ccna-lab.git
cd ccna-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m ccna_lab_builder.app
```

macOS helper:

```bash
./scripts/run_mac.sh
```

## Recommended workflow

1. Start with your already deployed EVE-NG server.
2. Install CCNA EVE Lab Builder on your Windows or Mac workstation.
3. Connect the application to EVE-NG.
4. Import or scan IOSv and IOSvL2.
5. Build `CCNA-MASTER-LAB`.
6. Select a training lab and create a fresh scenario lab.
7. Start the nodes and configure the Cisco devices yourself.
8. Run **Validate Live**.
9. Troubleshoot failed checks and repeat.

## Project layout

```text
ccna-lab/
├── ccna_lab_builder/
│   ├── app.py
│   ├── core/
│   ├── data/scenarios.json
│   └── gui/
├── deploy/
├── docs/
├── tests/
├── scripts/
├── .github/
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Documentation

- [Application installation](docs/INSTALLATION.md)
- [Existing EVE-NG integration](docs/EVE-NG.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Training labs](docs/LABS.md)
- [Validation](docs/VALIDATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Desktop deployment](docs/DEPLOYMENT.md)
- [Windows deployment](docs/DEPLOYMENT-WINDOWS.md)
- [macOS deployment](docs/DEPLOYMENT-MACOS.md)
- [Déploiement en français](docs/DEPLOIEMENT-FR.md)
- [GitHub publishing](docs/GITHUB.md)
- [Contributing](CONTRIBUTING.md)

## Compatibility note

The public EVE-NG API clearly documents authentication, lab/node/network creation, node start/stop/wipe/export, interface inspection, and topology inspection. The public page does **not clearly document a write endpoint for assigning an Ethernet interface to a network**. V4 therefore isolates automated cabling behind an explicit **experimental compatibility option**.

Without that option, V4 still creates the complete node layout and you can cable it once in the existing EVE-NG UI.

## Desktop installers

The deployment pipeline builds only the desktop application:

- Windows x64 `.exe` installer
- Windows portable `.zip`
- macOS Apple Silicon `.dmg`
- macOS Intel `.dmg`
- automatic GitHub Release builds

**No EVE-NG VM, ISO, OVA, hypervisor configuration or EVE-NG installer is bundled.**

See [Deployment](docs/DEPLOYMENT.md) and [Releasing](docs/RELEASING.md).

## Legal

This project is not affiliated with Cisco or EVE-NG. Cisco, IOS, IOSv and related marks belong to their respective owners. No vendor images are distributed with this repository.

MIT licensed.
