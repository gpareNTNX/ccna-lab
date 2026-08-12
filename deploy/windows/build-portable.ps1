param(
    [string]$Python = "python",
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
}

$Venv = Join-Path $Root ".venv-build-windows"
$PythonExe = Join-Path $Venv "Scripts\python.exe"

Write-Host "== CCNA EVE Lab Builder Windows build ==" -ForegroundColor Cyan
Write-Host "Version: $Version"

if (-not (Test-Path $PythonExe)) {
    & $Python -m venv $Venv
}

& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r (Join-Path $Root "requirements.txt")
& $PythonExe -m pip install "pyinstaller>=6.21,<7"

Remove-Item -Recurse -Force (Join-Path $Root "build") -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $Root "dist") -ErrorAction SilentlyContinue

$PyInstallerArgs = @(
    "--noconfirm", "--clean", "--windowed", "--onedir",
    "--name", "CCNA EVE Lab Builder",
    "--collect-data", "ccna_lab_builder",
    "--hidden-import", "tkinter",
    (Join-Path $Root "launcher.py")
)

$Icon = Join-Path $Root "deploy\assets\app.ico"
if (Test-Path $Icon) { $PyInstallerArgs = @("--icon", $Icon) + $PyInstallerArgs }

& $PythonExe -m PyInstaller @PyInstallerArgs

$Exe = Join-Path $Root "dist\CCNA EVE Lab Builder\CCNA EVE Lab Builder.exe"
if (-not (Test-Path $Exe)) { throw "PyInstaller did not create: $Exe" }

Write-Host "Portable application created: $Exe" -ForegroundColor Green
