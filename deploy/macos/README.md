# macOS desktop application packaging

This directory packages **CCNA EVE Lab Builder for macOS**. It does not package or install EVE-NG.

V4.1 supports Apple Silicon (`arm64`) and Intel (`x86_64`). The GitHub workflow builds both client architectures automatically.

## Local build

```bash
./deploy/macos/build-all.sh
```

Outputs:

```text
dist/CCNA EVE Lab Builder.app
release/CCNA-EVE-Lab-Builder-macOS-<arch>-<version>.dmg
```

The installed app connects to an already deployed EVE-NG server using API + SSH. No EVE-NG server component is included in the app or DMG.

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
