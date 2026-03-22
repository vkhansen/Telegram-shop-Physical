# teardown.ps1 — Stop and remove all containers
# Usage:
#   .\teardown.ps1          — stop containers (preserves data)
#   .\teardown.ps1 -Clean   — stop containers AND remove volumes (wipes all data)

param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

Write-Host "=== Telegram Shop — Teardown ===" -ForegroundColor Cyan

if ($Clean) {
    Write-Host "Stopping containers and removing volumes..." -ForegroundColor Red
    docker-compose down -v
    Write-Host "All containers stopped. Volumes removed — DB, Redis, Tailscale state wiped." -ForegroundColor Red
} else {
    Write-Host "Stopping containers..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "All containers stopped. Volumes preserved." -ForegroundColor Green
}

Write-Host "=== Teardown complete ===" -ForegroundColor Cyan
