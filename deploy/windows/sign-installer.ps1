param(
    [Parameter(Mandatory=$true)][string]$Installer,
    [Parameter(Mandatory=$true)][string]$CertificateThumbprint,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)
$ErrorActionPreference = "Stop"
$Signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
if (-not $Signtool) { throw "signtool.exe was not found. Install the Windows SDK." }
& $Signtool.Source sign /sha1 $CertificateThumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 $Installer
& $Signtool.Source verify /pa /v $Installer
