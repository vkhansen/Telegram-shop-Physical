# rebuild.ps1 - Teardown and rebuild all Docker containers
# Includes WSL health check and auto-repair
# Usage:
#   .\rebuild.ps1          - rebuild everything, preserves DB/Redis data
#   .\rebuild.ps1 -Clean   - full teardown, removes volumes and all data
#   .\rebuild.ps1 -BotOnly - rebuild only the bot container

param(
    [switch]$Clean,
    [switch]$BotOnly
)

$ErrorActionPreference = "Continue"

# ---- WSL Health Check and Auto-Repair ----
function Test-AndRepairWSL {
    Write-Host "[WSL] Checking WSL health..." -ForegroundColor Cyan

    # Check if WSL is available
    $wslExists = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if (-not $wslExists) {
        Write-Host "[WSL] wsl.exe not found. Docker may not work." -ForegroundColor Red
        Write-Host "[WSL] Install WSL with: wsl --install" -ForegroundColor Yellow
        return $false
    }

    # Check WSL status
    $wslStatus = wsl --status 2>&1
    $wslStatusStr = "$wslStatus"

    if ($wslStatusStr -match "error|ERROR|failed") {
        Write-Host "[WSL] WSL reports errors. Attempting repair..." -ForegroundColor Yellow
        return (Repair-WSL)
    }

    # Try a simple WSL command to verify it works
    $testResult = wsl -e echo "ok" 2>&1
    $testStr = "$testResult"

    if ($testStr -match "error|ERROR|failed|getpwnam|getpwuid|I/O error") {
        Write-Host "[WSL] WSL is corrupted. Attempting repair..." -ForegroundColor Yellow
        return (Repair-WSL)
    }

    if ($testStr.Trim() -eq "ok") {
        Write-Host "[WSL] WSL is healthy" -ForegroundColor Green
        return $true
    }

    # Check if Docker Desktop WSL integration is working
    $dockerWsl = docker info 2>&1
    $dockerWslStr = "$dockerWsl"

    if ($dockerWslStr -match "error|Cannot connect|Is the docker daemon running") {
        Write-Host "[WSL] Docker daemon not responding. Attempting WSL repair..." -ForegroundColor Yellow
        return (Repair-WSL)
    }

    Write-Host "[WSL] WSL is healthy" -ForegroundColor Green
    return $true
}

function Repair-WSL {
    Write-Host "[WSL] Step 1/4: Shutting down WSL..." -ForegroundColor Yellow
    wsl --shutdown 2>$null
    Start-Sleep -Seconds 3

    # Try basic command after shutdown
    $test1 = wsl -e echo "ok" 2>&1
    if ("$test1".Trim() -eq "ok") {
        Write-Host "[WSL] Fixed after WSL restart" -ForegroundColor Green
        return $true
    }

    Write-Host "[WSL] Step 2/4: Updating WSL..." -ForegroundColor Yellow
    wsl --update 2>$null
    Start-Sleep -Seconds 5

    $test2 = wsl -e echo "ok" 2>&1
    if ("$test2".Trim() -eq "ok") {
        Write-Host "[WSL] Fixed after WSL update" -ForegroundColor Green
        return $true
    }

    Write-Host "[WSL] Step 3/4: Listing distributions..." -ForegroundColor Yellow
    $distros = wsl --list --quiet 2>&1
    $distroStr = "$distros"

    # Check if any distro is corrupted - try to re-register
    if ($distroStr -match "Ubuntu") {
        Write-Host "[WSL] Found Ubuntu. Attempting to terminate and restart..." -ForegroundColor Yellow
        wsl --terminate Ubuntu 2>$null
        Start-Sleep -Seconds 3

        $test3 = wsl -d Ubuntu -e echo "ok" 2>&1
        if ("$test3".Trim() -eq "ok") {
            Write-Host "[WSL] Fixed after Ubuntu restart" -ForegroundColor Green
            return $true
        }

        Write-Host "[WSL] Ubuntu is corrupted beyond restart fix." -ForegroundColor Red
        Write-Host "[WSL] To fully reset Ubuntu, run as Admin:" -ForegroundColor Yellow
        Write-Host "         wsl --unregister Ubuntu" -ForegroundColor White
        Write-Host "         wsl --install Ubuntu" -ForegroundColor White
    }

    Write-Host "[WSL] Step 4/4: Restarting Docker Desktop service..." -ForegroundColor Yellow
    $dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcess) {
        Write-Host "[WSL] Stopping Docker Desktop..." -ForegroundColor Yellow
        Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        Write-Host "[WSL] Starting Docker Desktop..." -ForegroundColor Yellow
        Start-Process "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
        Write-Host "[WSL] Waiting for Docker to start (30s)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30

        $test4 = docker info 2>&1
        if (-not ("$test4" -match "error|Cannot connect")) {
            Write-Host "[WSL] Docker is back up" -ForegroundColor Green
            return $true
        }
    }

    Write-Host "[WSL] Auto-repair failed. Manual steps:" -ForegroundColor Red
    Write-Host "  1. Open PowerShell as Admin" -ForegroundColor White
    Write-Host "  2. Run: wsl --shutdown" -ForegroundColor White
    Write-Host "  3. Run: wsl --unregister Ubuntu" -ForegroundColor White
    Write-Host "  4. Run: wsl --install Ubuntu" -ForegroundColor White
    Write-Host "  5. Restart Docker Desktop" -ForegroundColor White
    Write-Host "  6. Re-run this script" -ForegroundColor White
    return $false
}

# ---- Main Script ----
Write-Host "Telegram Shop - Rebuild" -ForegroundColor Cyan

$wslOk = Test-AndRepairWSL
if (-not $wslOk) {
    Write-Host "Cannot proceed without working WSL/Docker. Exiting." -ForegroundColor Red
    exit 1
}

if ($BotOnly) {
    Write-Host "[1/3] Stopping bot container..." -ForegroundColor Yellow
    docker kill telegram_shop_bot 2>$null
    docker-compose rm -f bot 2>$null

    Write-Host "[2/3] Rebuilding bot image..." -ForegroundColor Yellow
    docker-compose build --no-cache bot

    Write-Host "[3/3] Starting bot container..." -ForegroundColor Yellow
    docker-compose up -d bot

    Write-Host "Bot rebuilt successfully" -ForegroundColor Green
    docker-compose ps
    exit 0
}

Write-Host "[1/4] Force-stopping all containers..." -ForegroundColor Yellow
docker ps -q | ForEach-Object { docker kill $_ } 2>$null
docker-compose down --remove-orphans --timeout 5 2>$null

if ($Clean) {
    Write-Host "[2/4] Removing volumes and all data..." -ForegroundColor Red
    docker-compose down -v --timeout 5 2>$null
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
