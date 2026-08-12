# macOS desktop application deployment

This package installs **CCNA EVE Lab Builder on macOS**. It does not install or package EVE-NG.

## Runtime assumption

An EVE-NG server is already deployed and reachable from the Mac. After the application is installed, it connects to that existing server through the EVE API and SSH.

## Final artifacts

```text
CCNA-EVE-Lab-Builder-macOS-arm64-<version>.dmg
CCNA-EVE-Lab-Builder-macOS-x86_64-<version>.dmg
```

Use `arm64` for Apple Silicon and `x86_64` for Intel.

## Local build

```bash
./deploy/macos/build-all.sh
```

This creates the desktop `.app` with PyInstaller and the `.dmg` with Apple's built-in `hdiutil`. No EVE-NG VM or server component is copied into the DMG.

## Developer ID signing

```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAMID)"
./deploy/macos/build-app.sh
./deploy/macos/package-dmg.sh
```

## Apple notarization

```bash
export APPLE_ID="you@example.com"
export APPLE_TEAM_ID="ABCDE12345"
export APPLE_APP_PASSWORD="your-app-specific-password"
./deploy/macos/notarize-dmg.sh
```

The notarization script uses `xcrun notarytool submit`, then `xcrun stapler staple` and `validate`. Never store signing credentials in Git.

## GitHub Actions signing secrets

To let the included workflow produce signed and notarized DMGs, define these repository secrets:

```text
APPLE_CERTIFICATE_BASE64
APPLE_CERTIFICATE_PASSWORD
KEYCHAIN_PASSWORD
APPLE_SIGNING_IDENTITY
APPLE_ID
APPLE_TEAM_ID
APPLE_APP_PASSWORD
```

If these secrets are absent, the workflow still builds unsigned test DMGs of the desktop application.
