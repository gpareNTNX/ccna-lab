# Windows desktop application deployment

This package installs **CCNA EVE Lab Builder on Windows**. It does not install EVE-NG.

## Runtime assumption

An EVE-NG server is already deployed and reachable from the Windows workstation. After installation, the user enters that server's IP/FQDN, API credentials and SSH information in the application.

## Final artifacts

```text
CCNA-EVE-Lab-Builder-Windows-x64-<version>-Setup.exe
CCNA-EVE-Lab-Builder-Windows-x64-<version>-Portable.zip
```

## End-user prerequisites

- Windows 10/11 x64
- network access to the existing EVE-NG server

Python and Inno Setup are **build-machine requirements only**, not end-user requirements for the packaged installer.

## Build-machine prerequisites

- Windows 10/11 x64
- Python 3.10+
- Inno Setup 6

## Build

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\deploy\windows\build-all.ps1
```

`build-portable.ps1` uses a PyInstaller `onedir` bundle. `build-installer.ps1` then compiles the Inno Setup project through `ISCC.exe`.

## Enterprise deployment

Deploy the Windows client with your normal endpoint-management platform. EVE-NG remains a separately managed server-side dependency.

## Signing

No Authenticode private key is bundled. Sign the final installer with your organization's Windows code-signing certificate when required.
