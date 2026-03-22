# teardown-clean.ps1 - Stop all containers AND wipe all data
# Includes WSL health check
# Usage: .\teardown-clean.ps1
# WARNING: This deletes the database, Redis data, and Tailscale state!

$ErrorActionPreference = "Continue"

Write-Host "Telegram Shop - Full Teardown (WIPING ALL DATA)" -ForegroundColor Red

# Quick WSL/Docker check
$dockerCheck = docker info 2>&1
if ("$dockerCheck" -match "error|Cannot connect|Is the docker daemon running") {
    Write-Host "[WSL] Docker not responding. Restarting WSL..." -ForegroundColor Yellow
    wsl --shutdown 2>$null
    Start-Sleep -Seconds 3
    $retry = docker info 2>&1
    if ("$retry" -match "error|Cannot connect") {
        Write-Host "[WSL] Docker still down. Try restarting Docker Desktop manually." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Force-stopping all containers..." -ForegroundColor Yellow
docker ps -q | ForEach-Object { docker kill $_ } 2>$null
docker-compose down -v --remove-orphans --timeout 5 2>$null

Write-Host "All containers stopped. All volumes and data wiped." -ForegroundColor Red
