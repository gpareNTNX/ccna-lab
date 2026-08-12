# Desktop application deployment overview

V4.1 provides a deployment pipeline for the **CCNA EVE Lab Builder desktop application only**.

## Explicitly not included

The deployment pipeline does **not** build, install, provision or bundle:

- EVE-NG Community or Pro
- an EVE-NG VM / OVA / ISO
- VMware, ESXi, Proxmox, Hyper-V or another hypervisor
- nested virtualization configuration
- Cisco IOSv/IOSvL2 images

EVE-NG is assumed to be already deployed and reachable.

## What is deployed

The desktop package contains the application and its local runtime dependencies so a workstation can connect to the existing EVE-NG server.

## Release matrix

| Client OS | Architecture | Application package |
|---|---|---|
| Windows 10/11 | x64 | Inno Setup `.exe` + portable ZIP |
| macOS | Apple Silicon / arm64 | `.dmg` containing `.app` |
| macOS | Intel / x86_64 | `.dmg` containing `.app` |

## Runtime relationship

```text
Desktop installer
      |
      v
CCNA EVE Lab Builder
      |
      | API + SSH
      v
Existing EVE-NG server
```

## Why separate client builds?

PyInstaller bundles Python and native libraries and is not a general cross-compiler. Windows is built on Windows, macOS Apple Silicon on an arm64 Mac runner, and macOS Intel on an Intel Mac runner.

## Automated release flow

```text
git tag v4.1.0
       |
       v
GitHub Actions
  |--- Windows x64 ---> Setup.exe + Portable.zip
  |--- macOS arm64 ---> arm64.dmg
  |--- macOS Intel ---> x86_64.dmg
       |
       v
GitHub Release
```

Those release artifacts install the client application only.
