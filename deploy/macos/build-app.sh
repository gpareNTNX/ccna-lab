#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
VERSION="${VERSION:-$(tr -d '[:space:]' < VERSION)}"
VENV="$ROOT/.venv-build-macos"

echo "== CCNA EVE Lab Builder macOS build =="
echo "Version: $VERSION"
echo "Architecture: $(uname -m)"

python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"
"$VENV/bin/python" -m pip install "pyinstaller>=6.21,<7"

rm -rf "$ROOT/build" "$ROOT/dist"
ARGS=(
  --noconfirm --clean --windowed
  --name "CCNA EVE Lab Builder"
  --collect-data ccna_lab_builder
  --hidden-import tkinter
  --osx-bundle-identifier "dev.npx25.ccna-eve-lab-builder"
)

if [[ -f "$ROOT/deploy/assets/app.icns" ]]; then
  ARGS+=(--icon "$ROOT/deploy/assets/app.icns")
fi
if [[ -n "${APPLE_SIGNING_IDENTITY:-}" ]]; then
  echo "Developer ID signing enabled."
  ARGS+=(--codesign-identity "$APPLE_SIGNING_IDENTITY")
fi

"$VENV/bin/python" -m PyInstaller "${ARGS[@]}" "$ROOT/launcher.py"
APP="$ROOT/dist/CCNA EVE Lab Builder.app"
[[ -d "$APP" ]] || { echo "App bundle not created: $APP" >&2; exit 1; }
echo "Created: $APP"
codesign --verify --deep --strict "$APP" || true
