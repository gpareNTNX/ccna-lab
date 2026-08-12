#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
VERSION="${VERSION:-$(tr -d '[:space:]' < VERSION)}"
ARCH="${ARCH_LABEL:-$(uname -m)}"
APP="$ROOT/dist/CCNA EVE Lab Builder.app"
RELEASE="$ROOT/release"
STAGE="$ROOT/build/dmg-stage-$ARCH"
DMG="$RELEASE/CCNA-EVE-Lab-Builder-macOS-$ARCH-$VERSION.dmg"

[[ -d "$APP" ]] || { echo "Run build-app.sh first." >&2; exit 1; }
rm -rf "$STAGE"
mkdir -p "$STAGE" "$RELEASE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
rm -f "$DMG"
hdiutil create -volname "CCNA EVE Lab Builder" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
echo "Created: $DMG"
