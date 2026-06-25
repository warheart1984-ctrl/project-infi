#!/usr/bin/env pwsh
# Apply Nexus TSR takeover: disconnect Daniel, persist routing, restart AAIS.
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [int]$AaisPort = 8000,
    [switch]$SkipRestart
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$online = Join-Path $RepoRoot ".runtime\online"
New-Item -ItemType Directory -Force -Path $online | Out-Null

$env:TSR_ROUTING_PATH = Join-Path $online "tsr-routing.json"
$env:CAB_STORE = Join-Path $online "cab-ledger.jsonl"
$env:AAIS_ONLINE_RUNTIME_DIR = $online
$env:NEXUS_OPS_CONSOLE_URL = "http://127.0.0.1:4000"
$env:LAWFUL_NOVA_REPO_ROOT = $RepoRoot
$env:PYTHONPATH = $RepoRoot

$PyExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PyExe)) {
    $PyExe = (Get-Command python -ErrorAction Stop).Source
}

Write-Host "Applying Nexus TSR takeover..." -ForegroundColor Cyan
& $PyExe -c "from src.aaes_os.tsr_routing import apply_nexus_takeover; import json; print(json.dumps(apply_nexus_takeover(reason='operator_nexus_takeover'), indent=2))"

if (-not $SkipRestart) {
    $conn = Get-NetTCPConnection -LocalPort $AaisPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        Write-Host "Restarting AAIS on port $AaisPort (PID $($conn.OwningProcess))..."
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    $dataDir = Join-Path $RepoRoot ".runtime\aais-data"
    Start-Process -FilePath $PyExe `
        -ArgumentList @("-m", "aais", "start", "--data-dir", $dataDir, "--preset", "mock", "--no-browser", "--port", "$AaisPort") `
        -WorkingDirectory $RepoRoot `
        -WindowStyle Hidden
    Start-Sleep -Seconds 2
    $health = $null
    for ($i = 0; $i -lt 15; $i++) {
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$AaisPort/health" -TimeoutSec 5
            if ($health.status) { break }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    if (-not $health) {
        throw "AAIS failed to become healthy on port $AaisPort within 30s"
    }
    Write-Host "AAIS health: $($health.status)"
}

try {
    $tsr = Invoke-RestMethod -Uri "http://127.0.0.1:4000/tsr" -TimeoutSec 5
    Write-Host "Nexus TSR owner: $($tsr.tsr.tsrOwner)"
    Write-Host "Daniel connector: $($tsr.tsr.connectors.daniel)"
} catch {
    Write-Host "Nexus /tsr not yet visible (restart ops-console if needed): $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "Takeover artifact: $env:TSR_ROUTING_PATH" -ForegroundColor Green
