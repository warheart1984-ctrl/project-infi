#Requires -Version 5.1
<#
.SYNOPSIS
  Poll /health until AAIS reports ai_status=initialized (production boot complete).

.PARAMETER TimeoutSeconds
  Maximum wait time (default 900s for first local model download).

.EXAMPLE
  .\scripts\wait-production-health.ps1 -Port 8000
#>
param(
    [int]$Port = 8000,
    [int]$TimeoutSeconds = 900,
    [int]$IntervalSeconds = 5
)

$ErrorActionPreference = "Stop"
$uri = "http://127.0.0.1:$Port/health"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$attempt = 0

Write-Host "Waiting for $uri (ai_status=initialized, timeout=${TimeoutSeconds}s)..." -ForegroundColor Cyan

while ((Get-Date) -lt $deadline) {
    $attempt++
    try {
        $resp = Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec 10
        $ai = [string]$resp.ai_status
        $mode = [string]$resp.active_model_mode
        Write-Host "  [$attempt] ai_status=$ai active_model_mode=$mode"
        if ($ai -eq "initialized") {
            Write-Host "Production health OK." -ForegroundColor Green
            $resp | ConvertTo-Json -Depth 6
            exit 0
        }
    } catch {
        Write-Host "  [$attempt] not ready: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds $IntervalSeconds
}

Write-Host "Timed out waiting for production health on port $Port" -ForegroundColor Red
exit 1
