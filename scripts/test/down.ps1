# scripts/test/down.ps1 - Tear down the test stack
# Usage:
#   .\scripts\test\down.ps1         - stop containers, keep test volumes
#   .\scripts\test\down.ps1 -Clean  - stop and wipe test volumes

param([switch]$Clean)

$ErrorActionPreference = "Continue"
$root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $root

Write-Host "[test-down] Stopping test stack..." -ForegroundColor Yellow

if ($Clean) {
    docker compose -f docker-compose.yml -f docker-compose.test.yml down -v --remove-orphans --timeout 5
    Write-Host "[test-down] Test containers stopped and volumes wiped" -ForegroundColor Red
} else {
    docker compose -f docker-compose.yml -f docker-compose.test.yml down --remove-orphans --timeout 5
    Write-Host "[test-down] Test containers stopped, volumes preserved" -ForegroundColor Green
}
