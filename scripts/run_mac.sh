#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTHON_VERSION="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

if ! "$PYTHON_BIN" -c 'import tkinter' >/dev/null 2>&1; then
  echo
  echo "ERROR: Tkinter is not available for $PYTHON_BIN (Python $PYTHON_VERSION)."
  echo
  if command -v brew >/dev/null 2>&1; then
    echo "This is common with Homebrew Python on macOS. Install the matching Tkinter formula:"
    echo
    echo "  brew install python-tk@$PYTHON_VERSION"
    echo
    echo "Then verify it with:"
    echo
    echo "  $PYTHON_BIN -m tkinter"
  else
    echo "Install a Python build that includes Tkinter, then run this script again."
  fi
  exit 1
fi

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c 'import tkinter; print(f"Tkinter OK (Tk {tkinter.TkVersion})")'
python -m ccna_lab_builder.app
