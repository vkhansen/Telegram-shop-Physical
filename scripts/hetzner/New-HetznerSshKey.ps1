# Unique ed25519 key for the Falkenstein (Germany) VPS. Never reuse GitHub or default id_ed25519.
# Usage: .\scripts\hetzner\New-HetznerSshKey.ps1

[CmdletBinding()]
param(
    [string]$Name = "hetzner-fsn-telegram-shop",
    [string]$Comment = "hetzner-fsn-telegram-shop"
)

$ErrorActionPreference = "Stop"
$sshDir = Join-Path $env:USERPROFILE ".ssh"
$private = Join-Path $sshDir "${Name}_ed25519"
$public = "${private}.pub"

if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir | Out-Null
}

if (Test-Path $private) {
    Write-Error "Key already exists: $private  — pick -Name or rotate by renaming the old files first."
}

ssh-keygen -t ed25519 -f $private -C $Comment -N '""'
if ($IsWindows -or $env:OS -match "Windows") {
    icacls $private /inheritance:r /grant:r "${env:USERNAME}:R" | Out-Null
}

Write-Host "Private (keep on this PC only): $private"
Write-Host "Public (paste into Hetzner SSH keys): $public"
Write-Host ""
Get-Content $public
