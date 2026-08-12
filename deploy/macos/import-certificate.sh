#!/bin/bash
set -euo pipefail
: "${APPLE_CERTIFICATE_BASE64:?Set APPLE_CERTIFICATE_BASE64}"
: "${APPLE_CERTIFICATE_PASSWORD:?Set APPLE_CERTIFICATE_PASSWORD}"
: "${KEYCHAIN_PASSWORD:?Set KEYCHAIN_PASSWORD}"

export CERT_PATH="${RUNNER_TEMP:-/tmp}/ccna-builder-developer-id.p12"
KEYCHAIN_PATH="${RUNNER_TEMP:-/tmp}/ccna-builder-signing.keychain-db"

python3 - <<'PY2'
import base64, os
from pathlib import Path
Path(os.environ["CERT_PATH"]).write_bytes(base64.b64decode(os.environ["APPLE_CERTIFICATE_BASE64"]))
PY2
security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
security import "$CERT_PATH" -P "$APPLE_CERTIFICATE_PASSWORD" -A -t cert -f pkcs12 -k "$KEYCHAIN_PATH"
security set-key-partition-list -S apple-tool:,apple: -s -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
security list-keychain -d user -s "$KEYCHAIN_PATH"
rm -f "$CERT_PATH"
echo "Developer ID certificate imported into temporary keychain."
