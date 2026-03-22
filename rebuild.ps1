# rebuild.ps1 - Teardown and rebuild all Docker containers
# Usage:
#   .\rebuild.ps1          - rebuild everything, preserves DB/Redis data
#   .\rebuild.ps1 -Clean   - full teardown, removes volumes and all data
#   .\rebuild.ps1 -BotOnly - rebuild only the bot container

param(
    [switch]$Clean,
    [switch]$BotOnly
)

$ErrorActionPreference = "Stop"

Write-Host "Telegram Shop - Rebuild" -ForegroundColor Cyan

if ($BotOnly) {
    Write-Host "[1/3] Stopping bot container..." -ForegroundColor Yellow
    docker-compose stop bot

    Write-Host "[2/3] Rebuilding bot image..." -ForegroundColor Yellow
    docker-compose build --no-cache bot

    Write-Host "[3/3] Starting bot container..." -ForegroundColor Yellow
    docker-compose up -d bot

    Write-Host "Bot rebuilt successfully" -ForegroundColor Green
    docker-compose ps
    exit 0
}

Write-Host "[1/4] Stopping all containers..." -ForegroundColor Yellow
docker-compose down

if ($Clean) {
    Write-Host "[2/4] Removing volumes and all data..." -ForegroundColor Red
    docker-compose down -v
    Write-Host "WARNING: All data has been wiped!" -ForegroundColor Red
} else {
    Write-Host "[2/4] Keeping volumes, DB data preserved" -ForegroundColor Green
}

Write-Host "[3/4] Rebuilding images..." -ForegroundColor Yellow
docker-compose build --no-cache

Write-Host "[4/4] Starting all containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Rebuild complete" -ForegroundColor Green
docker-compose ps
