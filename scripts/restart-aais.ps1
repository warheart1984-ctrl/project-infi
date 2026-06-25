#Requires -Version 5.1
<#
.SYNOPSIS
  Restart AAIS on port 8000 with current .novarc.ps1 environment (kill switches, RSL path).
#>
param(
    [int]$Port = 8000,
    [string]$Preset = "mock",
    [switch]$LocalReal
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path $PSScriptRoot -Parent
if (Test-Path "$env:USERPROFILE\.novarc.ps1") {
    . "$env:USERPROFILE\.novarc.ps1"
}
$env:LAWFUL_NOVA_REPO_ROOT = $Repo

$conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    $name = if ($proc) { $proc.ProcessName } else { "unknown" }
    if ($name -match '^(python|uvicorn)$') {
        Write-Host "Stopping AAIS pid=$($conn.OwningProcess) $name on port $Port"
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Port $Port held by $name (pid=$($conn.OwningProcess)) - not killing; start may fail if port busy"
    }
}

$py = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Missing $py" }

if ($LocalReal) {
    $Preset = "laptop"
    $env:AAIS_FORCE_LOCAL_MODEL = "1"
    # Dev escape hatch when persisted CSR hydration fails — see docs/agentic/README.md
    $env:CONSTITUTIONAL_BOOT_SKIP = "1"
    Write-Host "LocalReal: preset=laptop AAIS_FORCE_LOCAL_MODEL=1 (on-device Qwen)"
}

Write-Host "Starting AAIS preset=$Preset with kill-switch env..."
Start-Process -FilePath $py -ArgumentList @(
    "-m", "aais", "start",
    "--data-dir", (Join-Path $Repo ".runtime\aais-data"),
    "--preset", $Preset,
    "--no-browser",
    "--port", "$Port"
) -WorkingDirectory $Repo -WindowStyle Hidden

$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline) {
    try {
        $null = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 2
        Write-Host "AAIS healthy on http://127.0.0.1:$Port/health"
        exit 0
    } catch {
        Start-Sleep -Seconds 1
    }
}
throw "AAIS did not become healthy within 30s"
