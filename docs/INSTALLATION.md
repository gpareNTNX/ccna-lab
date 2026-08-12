# Installation

## Requirements

- Python 3.10+
- EVE-NG reachable from your workstation
- SSH access to EVE-NG
- An EVE-NG account usable through the API
- Legal IOSv and IOSvL2 QEMU image files
- Hardware virtualization enabled on the EVE-NG host

## macOS

```bash
git clone <YOUR-REPOSITORY-URL>
cd ccna-eve-lab-builder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m ccna_lab_builder.app
```

Or:

```bash
./scripts/run_mac.sh
```

## Linux

```bash
./scripts/run_linux.sh
```

If Tkinter is not installed on Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3-tk
```

## First connection

In **EVE-NG** tab:

- Host: EVE-NG IP/FQDN
- Username: your EVE/SSH user
- Password: entered only in memory
- SSH port: normally 22
- HTTPS: enable for EVE-NG Pro when appropriate

The application intentionally does **not** save your password.
