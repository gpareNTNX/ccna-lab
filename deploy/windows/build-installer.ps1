param([string]$Version = "")

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
}

$Exe = Join-Path $Root "dist\CCNA EVE Lab Builder\CCNA EVE Lab Builder.exe"
if (-not (Test-Path $Exe)) { throw "Portable build not found. Run build-portable.ps1 first." }

$Candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$ISCC = $Candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $ISCC) {
    $Cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($Cmd) { $ISCC = $Cmd.Source }
}
if (-not $ISCC) { throw "Inno Setup 6 / ISCC.exe was not found." }

New-Item -ItemType Directory -Force (Join-Path $Root "release") | Out-Null
& $ISCC "/DAppVersion=$Version" (Join-Path $Root "deploy\windows\installer.iss")
Write-Host "Windows installer created in release\" -ForegroundColor Green
