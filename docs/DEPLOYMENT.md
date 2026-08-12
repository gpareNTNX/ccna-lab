# Deployment overview

V4.1 adds a complete desktop deployment pipeline.

## Release matrix

| OS | Architecture | Package |
|---|---|---|
| Windows 10/11 | x64 | Inno Setup `.exe` |
| macOS | Apple Silicon / arm64 | `.dmg` containing `.app` |
| macOS | Intel / x86_64 | `.dmg` containing `.app` |

## Why separate builds?

PyInstaller bundles Python and native libraries and is not a general cross-compiler. Windows is built on Windows, macOS Apple Silicon on an arm64 Mac runner, and macOS Intel on an Intel Mac runner.

## Automated release flow

```text
git tag v4.1.0
       |
       v
GitHub Actions
  |--- Windows x64 ---> Setup.exe
  |--- macOS arm64 ---> arm64.dmg
  |--- macOS Intel ---> x86_64.dmg
       |
       v
GitHub Release
```

Unsigned builds are useful for testing. For public distribution, use platform signing; on macOS use Developer ID signing and Apple notarization.
