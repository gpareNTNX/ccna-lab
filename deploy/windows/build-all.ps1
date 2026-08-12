param([string]$Python = "python", [string]$Version = "")
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "build-portable.ps1") -Python $Python -Version $Version
& (Join-Path $PSScriptRoot "build-portable-zip.ps1") -Version $Version
& (Join-Path $PSScriptRoot "build-installer.ps1") -Version $Version
