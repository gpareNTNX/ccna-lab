# Deployment package

This directory contains everything needed to produce installable builds of the application.

## Outputs

| Platform | Architecture | Output |
|---|---|---|
| Windows | x64 | Portable application folder + Inno Setup `.exe` installer |
| macOS | Apple Silicon / arm64 | `.app` + `.dmg` |
| macOS | Intel / x86_64 | `.app` + `.dmg` |

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

Run **Build Installers** manually from GitHub Actions, or create a version tag:

```bash
git tag v4.1.0
git push origin v4.1.0
```

A tag build creates a GitHub Release containing Windows x64, macOS Apple Silicon, and macOS Intel packages.
