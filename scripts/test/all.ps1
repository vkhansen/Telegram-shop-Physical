# scripts/test/all.ps1 - Full cycle: up -> run -> down
# Usage:
#   .\scripts\test\all.ps1
#   .\scripts\test\all.ps1 -Suite all
#   .\scripts\test\all.ps1 -Suite e2e -Clean

param(
    [ValidateSet("unit", "integration", "e2e", "all", "default")]
    [string]$Suite = "default",
    [string]$K = "",
    [switch]$Clean,
    [switch]$NoCov
)

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot

& "$scriptDir\up.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[test-all] up.ps1 failed, aborting" -ForegroundColor Red
    exit $LASTEXITCODE
}

try {
    & "$scriptDir\run.ps1" -Suite $Suite -K $K -NoCov:$NoCov
    $runExit = $LASTEXITCODE
} finally {
    & "$scriptDir\down.ps1" -Clean:$Clean
}

if ($runExit -ne 0) {
    Write-Host "[test-all] Tests failed with exit code $runExit" -ForegroundColor Red
} else {
    Write-Host "[test-all] Full cycle completed successfully" -ForegroundColor Green
}
exit $runExit
