# Windows deployment

## Final artifact

```text
CCNA-EVE-Lab-Builder-Windows-x64-<version>-Setup.exe
```

## Prerequisites

- Windows 10/11 x64
- Python 3.10+
- Inno Setup 6

## Build

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\deploy\windows\build-all.ps1
```

`build-portable.ps1` uses a PyInstaller `onedir` bundle for fast startup and easier troubleshooting. `build-installer.ps1` then compiles the Inno Setup project through `ISCC.exe`.

## Enterprise deployment

Inno Setup supports command-line installation options. Use the flags required by your management platform and test them in your environment.

## Signing

No Authenticode private key is bundled. Sign the final installer with your organization's Windows code-signing certificate when required.

## Portable ZIP

The Windows build also produces:

```text
CCNA-EVE-Lab-Builder-Windows-x64-<version>-Portable.zip
```

This is useful when you do not want to run an installer.
