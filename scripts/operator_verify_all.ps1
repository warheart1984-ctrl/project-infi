#Requires -Version 5.1
<#
.SYNOPSIS
  Full operator verification: audit, red team, UL smoke, operator E2E.

.EXAMPLE
  .\scripts\operator_verify_all.ps1
  .\scripts\operator_verify_all.ps1 -RestartAais
#>
param(
    [switch]$RestartAais,
    [switch]$RestartOperator,
    [switch]$SkipE2e
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path $PSScriptRoot -Parent
Set-Location $Repo

if (Test-Path "$env:USERPROFILE\.novarc.ps1") { . "$env:USERPROFILE\.novarc.ps1" }
$env:LAWFUL_NOVA_REPO_ROOT = $Repo

if ($RestartAais) {
    & "$Repo\scripts\restart-aais.ps1"
}

if ($RestartOperator) {
    & "$Repo\scripts\restart-operator-stack.ps1"
}

& "$Repo\scripts\start-nova-stack.ps1" | Out-Null

$failed = @()

Write-Host "`n==> production audit" -ForegroundColor Cyan
& "$Repo\scripts\e_drive_production_audit.ps1" -JsonOut "$Repo\.runtime\e_drive_audit.json"
if ($LASTEXITCODE -ne 0) { $failed += "audit" }

Write-Host "`n==> operator red team" -ForegroundColor Cyan
& "$Repo\scripts\operator_red_team.ps1" -JsonOut "$Repo\.runtime\operator_red_team.json"
if ($LASTEXITCODE -ne 0) { $failed += "red_team" }

$py = Join-Path $Repo ".venv\Scripts\python.exe"

Write-Host "`n==> UL smoke" -ForegroundColor Cyan
& $py -m tools.ul.smoke 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { $failed += "ul_smoke" }

if (-not $SkipE2e) {
    Write-Host "`n==> operator E2E" -ForegroundColor Cyan
    $env:OPERATOR_E2E_SKIP_DESKTOP = "1"
    & $py "$Repo\scripts\run_operator_e2e_validation.py" 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { $failed += "operator_e2e" }
}

if ($failed.Count -gt 0) {
    Write-Host "`nVERIFY FAILED: $($failed -join ', ')" -ForegroundColor Red
    exit 1
}
Write-Host "`nVERIFY ALL PASSED" -ForegroundColor Green
exit 0
