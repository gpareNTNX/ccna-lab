# Windows desktop application packaging

This directory packages **CCNA EVE Lab Builder for Windows**. It does not package or install EVE-NG.

The release artifact is:

```text
CCNA-EVE-Lab-Builder-Windows-x64-<version>-Setup.exe
```

The installer provides Start Menu integration, optional Desktop shortcut, uninstall support, and optional post-install launch. After launch, the application connects to an existing EVE-NG server.

## Build-machine prerequisites

- Windows 10/11 x64
- Python 3.10+
- Inno Setup 6

## Build everything

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\deploy\windows\build-all.ps1
```

For public enterprise distribution, Authenticode-sign the final installer with your organization's certificate. Never commit a private signing key.
