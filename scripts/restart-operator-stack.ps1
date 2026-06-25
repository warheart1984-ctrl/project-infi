#Requires -Version 5.1
<#
.SYNOPSIS
  Restart lawful brain (:8791) and operator kernel (:8790) after code changes.
#>
$ErrorActionPreference = "Stop"
$Repo = Split-Path $PSScriptRoot -Parent
if (Test-Path "$env:USERPROFILE\.novarc.ps1") {
    . "$env:USERPROFILE\.novarc.ps1"
}
$env:LAWFUL_NOVA_REPO_ROOT = $Repo
$env:PYTHONPATH = $Repo

function Stop-PortListener([int]$Port) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $conn) { return }
    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    $name = if ($proc) { $proc.ProcessName } else { "unknown" }
    if ($name -match '^python$') {
        Write-Host "Stopping $name pid=$($conn.OwningProcess) on port $Port"
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    } else {
        Write-Host "Port $Port held by $name (pid=$($conn.OwningProcess)) - not killing"
    }
}

Stop-PortListener 8790
Stop-PortListener 8791

& "$Repo\scripts\start-nova-stack.ps1" -OperatorOnly | Out-Host

$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline) {
    try {
        $null = Invoke-RestMethod "http://127.0.0.1:8790/health" -TimeoutSec 2
        $null = Invoke-RestMethod "http://127.0.0.1:8791/health" -TimeoutSec 2
        Write-Host "Operator stack healthy (8790 + 8791)"
        exit 0
    } catch {
        Start-Sleep -Seconds 1
    }
}
throw "Operator stack did not become healthy within 30s"
