# Desktop application deployment package

This directory builds installable packages for **CCNA EVE Lab Builder only**.

> EVE-NG is an existing external server dependency. Nothing in this directory installs, provisions, packages or deploys EVE-NG.

## Outputs

| Client platform | Architecture | Output |
|---|---|---|
| Windows | x64 | Portable application folder/ZIP + Inno Setup `.exe` installer |
| macOS | Apple Silicon / arm64 | `.app` + `.dmg` |
| macOS | Intel / x86_64 | `.app` + `.dmg` |

The installed desktop application connects to the pre-existing EVE-NG server through API + SSH.

PyInstaller is not a cross-compiler. Build each target on its corresponding operating system. The included GitHub Actions workflow does this automatically.

## Local builds

### Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\deploy\windows\build-all.ps1
```

### macOS

```bash
chmod +x deploy/macos/*.sh
./deploy/macos/build-all.sh
```

## Automated GitHub builds

Run **Build Installers** manually from GitHub Actions, or create a version tag. The resulting release contains client application packages only.
