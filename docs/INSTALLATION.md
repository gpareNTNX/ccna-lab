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

### macOS with Homebrew Python

Homebrew packages Tkinter separately from Python. If you use a Homebrew Python installation, install the Tkinter formula matching the interpreter's major/minor version before launching the GUI.

For Python 3.14:

```bash
brew install python-tk@3.14
```

Verify Tkinter:

```bash
python3 -m tkinter
```

A small Tk window should open. You can also verify it without opening the application:

```bash
python3 -c 'import tkinter; print(tkinter.TkVersion)'
```

Then install and run from source:

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

The helper script now checks Tkinter before creating/using the virtual environment. If Tkinter is missing from a Homebrew Python installation, it prints the exact `brew install python-tk@<major.minor>` command for that interpreter.

### macOS error: `No module named '_tkinter'`

If you see:

```text
ModuleNotFoundError: No module named '_tkinter'
```

and your interpreter is Python 3.14, run:

```bash
brew install python-tk@3.14
python3 -m tkinter
```

If `.venv` already exists, reactivate it and retry:

```bash
source .venv/bin/activate
python -m ccna_lab_builder.app
```

### Linux

```bash
./scripts/run_linux.sh
```

On Debian/Ubuntu, if Tkinter is missing:

```bash
sudo apt update
sudo apt install python3-tk
```

## First connection

In the **EVE-NG** tab, enter the connection information for the existing server:

- Host: existing EVE-NG IP/FQDN
- Username: EVE/SSH user
- Password: entered only in memory
- SSH port: normally 22
- HTTPS: enable for EVE-NG Pro when appropriate

The application intentionally does **not** save your password.
