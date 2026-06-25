#Requires -Version 5.1
<#
.SYNOPSIS
  Start the Project-Infinity1 agentic coding stack: Nova API, operator kernel, lawful brain, AAIS (real local).
.DESCRIPTION
  Template entry point aligned with agentic-coding-agent + lawful-nova-shell.
  Run verify-nova-local.ps1 after this for Nemotron + lawful-nova checks.
#>
param(
    [switch]$SkipAais,
    [switch]$QuickVerify
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "Project-Infinity1 agentic coding stack" -ForegroundColor Cyan
Write-Host "  Template: agentic-coding-agent -> nova-mission-002/"
Write-Host "  Agents:   AGENTS.md"
Write-Host ""

& (Join-Path $Root "scripts\start-nova-stack.ps1")

if (-not $SkipAais) {
    & (Join-Path $Root "scripts\restart-aais.ps1") -LocalReal
}

$gate = Join-Path $Root "lawful-nova-shell\scripts\nova_productization_gate.py"
$py = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $py) {
    Write-Host ""
    Write-Host "Productization gate:" -ForegroundColor Cyan
    & $py $gate
}

$verify = Join-Path $Root "scripts\verify-nova-local.ps1"
if (Test-Path $verify) {
    Write-Host ""
    $verifyArgs = if ($QuickVerify) { @("-Quick") } else { @() }
    & $verify @verifyArgs
}

Write-Host ""
Write-Host "Stack ready. Mission #002: cd nova-mission-002 && npm test" -ForegroundColor Green
Write-Host "Docs: docs/agentic/README.md"
