# CCNA 200-301 EVE-NG Lab Builder

A desktop GUI for building and practicing **CCNA 200-301** labs on **EVE-NG** using Cisco IOSv and IOSvL2 images that you provide legally.

## V4 highlights

- EVE-NG SSH + API connectivity
- IOSv / IOSvL2 image import
- Image inventory scan
- 9-device master topology
- Optional compatibility backend for automated cabling
- 20 CCNA practice scenarios
- Fresh scenario-lab creation
- Start / stop / wipe controls
- **Live validation** through Cisco console sessions tunneled over EVE-NG SSH
- GitHub Actions CI
- Unit tests
- Documentation for installation, architecture, scenarios, troubleshooting and contributing

> Cisco images are **not included** and must never be committed to this repository.

## Quick start

### macOS / Linux

```bash
git clone <YOUR-REPOSITORY-URL>
cd ccna-eve-lab-builder
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

1. Connect the app to EVE-NG.
2. Import or scan IOSv and IOSvL2.
3. Build `CCNA-MASTER-LAB`.
4. Select a training lab.
5. Create a fresh scenario lab.
6. Start the nodes.
7. Configure the Cisco devices yourself.
8. Run **Validate Live**.
9. Troubleshoot failed checks and repeat.

## Project layout

```text
ccna-eve-lab-builder/
├── ccna_lab_builder/
│   ├── app.py
│   ├── core/
│   ├── data/scenarios.json
│   └── gui/
├── docs/
├── tests/
├── scripts/
├── .github/
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Documentation

- [Installation](docs/INSTALLATION.md)
- [EVE-NG setup](docs/EVE-NG.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Training labs](docs/LABS.md)
- [Validation](docs/VALIDATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [GitHub publishing](docs/GITHUB.md)
- [Contributing](CONTRIBUTING.md)

## Compatibility note

The public EVE-NG API clearly documents authentication, lab/node/network creation, node start/stop/wipe/export, interface inspection, and topology inspection. The public page does **not clearly document a write endpoint for assigning an Ethernet interface to a network**. V4 therefore isolates automated cabling behind an explicit **experimental compatibility option**.

Without that option, V4 still creates the complete node layout and you can cable it once in the EVE-NG UI.

## Legal

This project is not affiliated with Cisco or EVE-NG. Cisco, IOS, IOSv and related marks belong to their respective owners. No vendor images are distributed with this repository.

MIT licensed.

## Desktop installers

V4.1 includes a complete packaging pipeline:

- Windows x64 `.exe` installer
- macOS Apple Silicon `.dmg`
- macOS Intel `.dmg`
- automatic GitHub Release builds

See [Deployment](docs/DEPLOYMENT.md), [Windows deployment](docs/DEPLOYMENT-WINDOWS.md), [macOS deployment](docs/DEPLOYMENT-MACOS.md), and [Releasing](docs/RELEASING.md).

To publish a release:

```bash
git tag v4.1.0
git push origin v4.1.0
```

GitHub Actions builds the platform-specific packages because PyInstaller needs to run on the target operating system.
