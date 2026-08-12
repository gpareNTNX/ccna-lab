#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
VERSION="${VERSION:-$(tr -d '[:space:]' < VERSION)}"
ARCH="${ARCH_LABEL:-$(uname -m)}"
DMG="${DMG_PATH:-$ROOT/release/CCNA-EVE-Lab-Builder-macOS-$ARCH-$VERSION.dmg}"

: "${APPLE_ID:?Set APPLE_ID}"
: "${APPLE_TEAM_ID:?Set APPLE_TEAM_ID}"
: "${APPLE_APP_PASSWORD:?Set APPLE_APP_PASSWORD to an app-specific password}"
[[ -f "$DMG" ]] || { echo "DMG not found: $DMG" >&2; exit 1; }

xcrun notarytool submit "$DMG" \
  --apple-id "$APPLE_ID" \
  --team-id "$APPLE_TEAM_ID" \
  --password "$APPLE_APP_PASSWORD" \
  --wait
xcrun stapler staple "$DMG"
xcrun stapler validate "$DMG"
echo "Notarized: $DMG"
