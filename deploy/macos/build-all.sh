#!/bin/bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
"$DIR/build-app.sh"
"$DIR/package-dmg.sh"
if [[ "${NOTARIZE:-0}" == "1" ]]; then
  "$DIR/notarize-dmg.sh"
fi
