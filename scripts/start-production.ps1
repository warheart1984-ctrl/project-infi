#Requires -Version 5.1
<#
.SYNOPSIS
  Verify and start the canonical production stack on E:\project-infi.
#>
$ErrorActionPreference = "Stop"
$Repo = Split-Path $PSScriptRoot -Parent

if (Test-Path "$env:USERPROFILE\.novarc.ps1") {
    . "$env:USERPROFILE\.novarc.ps1"
}
$env:LAWFUL_NOVA_REPO_ROOT = $Repo
Set-Location $Repo

Write-Host "=== Production start (canonical: $Repo) ===" -ForegroundColor Cyan

& "$Repo\scripts\e_drive_production_audit.ps1" -JsonOut "$Repo\.runtime\e_drive_audit.json"
$auditExit = $LASTEXITCODE

function Test-Health([string]$Url) {
    try { $null = Invoke-RestMethod $Url -TimeoutSec 2; return $true } catch { return $false }
}

$needNova = -not (Test-Health "http://127.0.0.1:8080/health")
$needAais = -not (Test-Health "http://127.0.0.1:8000/health")
$needStack = -not (Test-Health "http://127.0.0.1:8790/health")

if ($needNova -or $needStack) {
    Write-Host "`nStarting Nova + operator stack..." -ForegroundColor Cyan
    & "$Repo\scripts\start-nova-stack.ps1"
}

if ($needAais) {
    Write-Host "Starting AAIS (mock preset)..." -ForegroundColor Cyan
    $py = Join-Path $Repo ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { throw "Missing $py - run .\scripts\start-infinity1.ps1 first" }
    Start-Process -FilePath $py -ArgumentList @(
        "-m", "aais", "start",
        "--data-dir", (Join-Path $Repo ".runtime\aais-data"),
        "--preset", "mock",
        "--no-browser",
        "--port", "8000"
    ) -WorkingDirectory $Repo -WindowStyle Hidden
    Start-Sleep -Seconds 4
} else {
    # Stale AAIS may lack kill-switch env; probe /agent/run for fast 503
    $py = Join-Path $Repo ".venv\Scripts\python.exe"
    if (Test-Path $py) {
        $probe = & $py -c "import json,urllib.error,urllib.request; u='http://127.0.0.1:8000/agent/run'; b=json.dumps({'goal':'probe','session_id':'probe'}).encode(); r=urllib.request.Request(u,data=b,method='POST',headers={'Content-Type':'application/json'});
try:
 urllib.request.urlopen(r,timeout=3); print('OPEN')
except urllib.error.HTTPError as e: print(e.code)
except Exception as e: print(type(e).__name__)" 2>&1
        if (($probe | Out-String).Trim() -ne '503') {
            Write-Host "AAIS missing kill-switch env - restarting..." -ForegroundColor Yellow
            & "$Repo\scripts\restart-aais.ps1"
        }
    }
}

Write-Host "`n=== URLs ===" -ForegroundColor Green
Write-Host "  Nova API:  http://127.0.0.1:8080/health"
Write-Host "  AAIS:      http://127.0.0.1:8000/health"
Write-Host "  Operator:  http://127.0.0.1:8000/operator"
Write-Host "  Jarvis:    http://127.0.0.1:8000/app/jarvis"
Write-Host "`nRe-audit: .\scripts\e_drive_production_audit.ps1"

if ($auditExit -ne 0) {
    Write-Host "`nAudit had failures - re-run after services settle." -ForegroundColor Yellow
    exit $auditExit
}