# macOS deployment

V4.1 supports Apple Silicon (`arm64`) and Intel (`x86_64`). Build on each target architecture; the GitHub workflow does both automatically.

## Local build

```bash
./deploy/macos/build-all.sh
```

Outputs:

```text
dist/CCNA EVE Lab Builder.app
release/CCNA-EVE-Lab-Builder-macOS-<arch>-<version>.dmg
```

## Developer ID signing

```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAMID)"
./deploy/macos/build-app.sh
./deploy/macos/package-dmg.sh
```

## Notarization

```bash
export APPLE_ID="you@example.com"
export APPLE_TEAM_ID="ABCDE12345"
export APPLE_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
./deploy/macos/notarize-dmg.sh
```

For public distribution outside the Mac App Store, use Developer ID signing and Apple notarization.
