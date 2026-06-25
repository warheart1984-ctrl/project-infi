#Requires -Version 5.1
<#
.SYNOPSIS
  Run AAIS production verification gates (runbook §3.5).

.DESCRIPTION
  Executes the same Python gates documented in docs/operations/AAIS_PRODUCTION_OPERATOR_RUNBOOK.md
  before calling a Tier-A deployment "production-ready".
#>
param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
$Root = if ($RepoRoot) { (Resolve-Path $RepoRoot).Path } else { Split-Path $PSScriptRoot -Parent }
$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

$gates = @(
    @{ Name = "production-hardening"; Script = Join-Path $Root ".github\scripts\check-production-hardening.py" },
    @{ Name = "infinity1-flagship"; Script = Join-Path $Root "tools\governance\run_infinity1_flagship_verification.py" },
    @{ Name = "ga-signoff"; Script = Join-Path $Root ".github\scripts\check-ga-signoff.py"; Args = @("--mode", "fail") },
    @{ Name = "wave6-seams"; PytestTarget = "tests/test_wave6_transition_seams.py" },
    @{ Name = "ai-preflight"; Script = Join-Path $Root "scripts\preflight_production_ai.py" }
)

$failed = @()
foreach ($gate in $gates) {
    Write-Host "==> $($gate.Name)" -ForegroundColor Cyan
    if ($gate.PytestTarget) {
        & $Py -m pytest $gate.PytestTarget -q
    } elseif ($gate.Args) {
        & $Py $gate.Script @($gate.Args)
    } else {
        & $Py $gate.Script
    }
    if ($LASTEXITCODE -ne 0) {
        $failed += $gate.Name
        Write-Host "FAIL: $($gate.Name) (exit $LASTEXITCODE)" -ForegroundColor Red
    } else {
        Write-Host "PASS: $($gate.Name)" -ForegroundColor Green
    }
}

if ($failed.Count -gt 0) {
    Write-Host "`nProduction gates FAILED: $($failed -join ', ')" -ForegroundColor Red
    exit 1
}
Write-Host "`nAll production gates PASSED." -ForegroundColor Green
exit 0
