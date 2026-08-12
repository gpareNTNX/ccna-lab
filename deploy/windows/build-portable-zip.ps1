param([string]$Version = "")
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
}
$Source = Join-Path $Root "dist\CCNA EVE Lab Builder\*"
$Release = Join-Path $Root "release"
$Zip = Join-Path $Release "CCNA-EVE-Lab-Builder-Windows-x64-$Version-Portable.zip"
New-Item -ItemType Directory -Force $Release | Out-Null
Remove-Item $Zip -Force -ErrorAction SilentlyContinue
Compress-Archive -Path $Source -DestinationPath $Zip -CompressionLevel Optimal
Write-Host "Portable ZIP created: $Zip" -ForegroundColor Green
