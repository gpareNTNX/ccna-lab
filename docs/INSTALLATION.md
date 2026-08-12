# Application installation

This document installs **CCNA EVE Lab Builder on the client workstation only**.

## Important assumption

**EVE-NG is already deployed and operational.** The application does not install or provision EVE-NG, a hypervisor, nested virtualization, or an EVE-NG VM.

## Application requirements

- Windows 10/11 or a supported macOS system for packaged builds; or Python 3.10+ when running from source
- network reachability to the existing EVE-NG server
- SSH access to EVE-NG
- an EVE-NG account usable through the API
- legal IOSv and IOSvL2 QEMU images if you want to import images from the GUI

Server-side EVE-NG deployment, VM sizing, CPU virtualization features, storage and upgrades are managed separately and are outside this project's installer.

## Packaged installation

For end users, prefer the GitHub Release package for the workstation:

- Windows x64: `Setup.exe` or portable ZIP
- macOS Apple Silicon: arm64 DMG
- macOS Intel: x86_64 DMG

These packages contain the desktop application only.

## From source: macOS / Linux

```bash
git clone https://github.com/gpareNTNX/ccna-lab.git
cd ccna-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m ccna_lab_builder.app
```

Or on macOS:

```bash
./scripts/run_mac.sh
```

## First connection

In the **EVE-NG** tab, enter the connection information for the existing server:

- Host: existing EVE-NG IP/FQDN
- Username: EVE/SSH user
- Password: entered only in memory
- SSH port: normally 22
- HTTPS: enable for EVE-NG Pro when appropriate

The application intentionally does **not** save your password.
