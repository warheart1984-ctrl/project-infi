param(
    [switch]$FrontendBuild,
    [switch]$RunFullApi
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Missing .venv\\Scripts\\python.exe. Rebuild the project venv with: py -3.12 -m venv .venv"
}

function Invoke-ExternalStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Label"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

Write-Host "AAIS preflight starting..."
Write-Host "Workspace: $root"
Write-Host "Python:    $python"

Invoke-ExternalStep -Label "Verify runtime" -Command {
    & (Join-Path $scriptDir "verify-python-runtime.ps1")
}

Invoke-ExternalStep -Label "Run protocol tests" -Command {
    & $python -m pytest -q .\tests\test_jarvis_protocol.py
}

if ($RunFullApi) {
    Invoke-ExternalStep -Label "Run full API suite" -Command {
        & $python -m pytest -q .\tests\test_api.py
    }
} else {
    Invoke-ExternalStep -Label "Run API contract slice" -Command {
        & $python -m pytest -q .\tests\test_api.py -k "jarvis_protocol_endpoint or preview_truth or protocol_endpoint or doctrine or guardrail or modular_provider_preview or guardrails_allow_override or caution_propagates"
    }
}

if ($FrontendBuild) {
    Invoke-ExternalStep -Label "Build frontend" -Command {
        Push-Location (Join-Path $root "frontend")
        try {
            npm.cmd run build
        } finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "AAIS preflight passed."
