# scripts/test/run.ps1 - Run the test suite
# Usage:
#   .\scripts\test\run.ps1                 - unit + integration (default)
#   .\scripts\test\run.ps1 -Suite unit
#   .\scripts\test\run.ps1 -Suite integration
#   .\scripts\test\run.ps1 -Suite e2e      - includes --run-e2e gate
#   .\scripts\test\run.ps1 -Suite all      - everything incl. e2e
#   .\scripts\test\run.ps1 -K "test_cart"  - pass -k expression to pytest

param(
    [ValidateSet("unit", "integration", "e2e", "all", "default")]
    [string]$Suite = "default",
    [string]$K = "",
    [switch]$NoCov
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $root

$pytestArgs = @()

switch ($Suite) {
    "unit"        { $pytestArgs += "tests/unit" }
    "integration" { $pytestArgs += "tests/integration" }
    "e2e"         { $pytestArgs += @("tests/e2e", "--run-e2e") }
    "all"         { $pytestArgs += @("tests", "--run-e2e") }
    "default"     { $pytestArgs += @("tests/unit", "tests/integration") }
}

if ($K -ne "") { $pytestArgs += @("-k", $K) }
if ($NoCov)    { $pytestArgs += @("--no-cov") }

Write-Host "[test-run] pytest $($pytestArgs -join ' ')" -ForegroundColor Cyan
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm bot python -m pytest @pytestArgs
exit $LASTEXITCODE
