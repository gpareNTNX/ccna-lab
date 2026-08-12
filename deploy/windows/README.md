# Windows deployment

The release artifact is:

```text
CCNA-EVE-Lab-Builder-Windows-x64-<version>-Setup.exe
```

The installer provides Start Menu integration, optional Desktop shortcut, uninstall support, and optional post-install launch.

## Prerequisites

- Windows 10/11 x64
- Python 3.10+
- Inno Setup 6

## Build everything

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\deploy\windows\build-all.ps1
```

Portable build only:

```powershell
.\deploy\windows\build-portable.ps1
```

Installer only:

```powershell
.\deploy\windows\build-installer.ps1
```

For public enterprise distribution, Authenticode-sign the final installer with your organization's certificate. Never commit a private signing key.
