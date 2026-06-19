# Start lawful brain + operator kernel for local development.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:PYTHONPATH = $Root
if (-not $env:OPERATOR_KERNEL_CONFIG) {
    $env:OPERATOR_KERNEL_CONFIG = Join-Path $Root "operator_kernel.config.yaml"
}
if (-not $env:AAIS_SIGNING_SECRET) {
    $env:AAIS_SIGNING_SECRET = "operator-kernel-dev-secret"
}
if (-not $env:AAIS_WORKSPACE_ROOT) {
    $env:AAIS_WORKSPACE_ROOT = Join-Path $Root ".runtime\e2e-operator-workspace"
}
if (-not $env:OPERATOR_AGENT_INTER_STEP_SLEEP_SEC) {
    $env:OPERATOR_AGENT_INTER_STEP_SLEEP_SEC = "2"
}
if (-not $env:OPERATOR_LAWFUL_PLANNER_FALLBACK) {
    $env:OPERATOR_LAWFUL_PLANNER_FALLBACK = "1"
}
if (-not $env:OPERATOR_E2E_CANCEL_WINDOW) {
    $env:OPERATOR_E2E_CANCEL_WINDOW = "1"
}

$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPy) {
    $PyExe = $VenvPy
    $PyArgs = @()
} else {
    $PythonLine = (& (Join-Path $PSScriptRoot "resolve_python.ps1")).Trim()
    if ($PythonLine -match '^(.+\.exe)\s+(-\S+.*)$') {
        $PyExe = $Matches[1]
        $PyArgs = $Matches[2] -split '\s+'
    } else {
        $PyExe = $PythonLine
        $PyArgs = @()
    }
}

Write-Host "Using Python: $PyExe"
Write-Host "Starting lawful brain on 127.0.0.1:8791 ..."
$brainArgs = $PyArgs + @("-m", "operator_kernel.lawful_brain")
Start-Process -FilePath $PyExe -ArgumentList $brainArgs -WorkingDirectory $Root -WindowStyle Minimized

Start-Sleep -Seconds 2

Write-Host "Starting operator kernel on 127.0.0.1:8790 ..."
$kernelArgs = $PyArgs + @("-m", "operator_kernel")
& $PyExe @kernelArgs
