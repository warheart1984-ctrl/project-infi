# Verify Operator v1.0 release artifacts on this machine.
param(
    [string]$DistRoot = "",
    [string]$KernelUrl = "http://127.0.0.1:8790"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $DistRoot) {
    $DistRoot = Join-Path $Root "dist\operator-desktop"
}

$failures = @()

function Test-PathExists($path, $label) {
    if (-not (Test-Path $path)) {
        $script:failures += "$label missing: $path"
        return $false
    }
    Write-Host "[ok] $label"
    return $true
}

Write-Host "=== Operator v1.0 release verification ==="
Test-PathExists (Join-Path $DistRoot "OperatorDesktop.exe") "OperatorDesktop.exe"
Test-PathExists (Join-Path $DistRoot "operator_kernel") "operator_kernel package"
Test-PathExists (Join-Path $DistRoot "nova") "nova package"
Test-PathExists (Join-Path $DistRoot "operator-surface\dist\index.html") "operator-surface UI"
Test-PathExists (Join-Path $Root "configs\memory\paths.json") "memory config"

$NovaExe = Join-Path $DistRoot "nova.exe"
if (Test-Path $NovaExe) {
    Write-Host "[ok] nova.exe"
    & $NovaExe --help 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $failures += "nova.exe --help failed"
    } else {
        Write-Host "[ok] nova.exe --help"
    }
} else {
    $VenvNova = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $VenvNova) {
        & $VenvNova -m nova.cli health --json 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[ok] nova.cli health (dev)"
        }
    }
}

try {
    $health = Invoke-RestMethod -Uri "$KernelUrl/health" -TimeoutSec 3
    if ($health.status -eq "ok") {
        Write-Host "[ok] kernel /health"
    } else {
        $failures += "kernel /health unexpected: $($health | ConvertTo-Json -Compress)"
    }
} catch {
    Write-Host "[warn] kernel not running at $KernelUrl (start with scripts/run_operator_kernel.ps1)"
}

$testsPy = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $testsPy) {
    Push-Location $Root
    & $testsPy -m pytest tests/operator_kernel/test_lawful_adapter.py -q
    if ($LASTEXITCODE -ne 0) {
        $failures += "planner unit tests failed"
    } else {
        Write-Host "[ok] planner unit tests"
    }
    Pop-Location
}

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "FAILED:"
    $failures | ForEach-Object { Write-Host "  - $_" }
    exit 1
}

Write-Host ""
Write-Host "All checks passed."
exit 0
