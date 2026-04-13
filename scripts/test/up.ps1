# scripts/test/up.ps1 - Bring up the test stack (db + redis only)
# The bot test runner is invoked separately by run.ps1 so local pytest
# can also target the dockerized dependencies.
# Usage: .\scripts\test\up.ps1

$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $root

Write-Host "[test-up] Starting test db + redis..." -ForegroundColor Cyan
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d db redis
if ($LASTEXITCODE -ne 0) {
    Write-Host "[test-up] docker compose up failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "[test-up] Waiting for db healthcheck..." -ForegroundColor Yellow
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    $status = docker inspect -f '{{.State.Health.Status}}' telegram_shop_db_test 2>$null
    if ($status -eq 'healthy') {
        Write-Host "[test-up] db is healthy" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 1
}

if ($status -ne 'healthy') {
    Write-Host "[test-up] db did not become healthy in time" -ForegroundColor Red
    exit 1
}

docker compose -f docker-compose.yml -f docker-compose.test.yml ps
Write-Host "[test-up] Test stack ready" -ForegroundColor Green
