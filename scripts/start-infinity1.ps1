#!/usr/bin/env pwsh
# Infinity 1 - install dependencies and start AAIS (default preset: real AI + Nova companion).
# Usage: .\scripts\start-infinity1.ps1
#        .\scripts\start-infinity1.ps1 -ReplaceExisting   # free port 8000 first
#        .\scripts\start-infinity1.ps1 -Preset laptop
#        .\scripts\start-infinity1.ps1 -Preset mock

param(
    [switch]$SkipInstall,
    [switch]$ReplaceExisting,
    [switch]$InstallReal,
    [ValidateSet("default", "production", "laptop", "mock")]
    [string]$Preset = "default",
    [int]$Port = 8000,
    [string]$DataDir = "./.runtime/aais-data"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Find-Python {
    $candidates = @(
        @{ Label = "py -3.10"; Exe = "py"; Args = @("-3.10") },
        @{ Label = "py -3"; Exe = "py"; Args = @("-3") },
        @{ Label = "Python 3.10"; Exe = "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"; Args = @() },
        @{ Label = "Python 3.12"; Exe = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"; Args = @() }
    )
    foreach ($c in $candidates) {
        if ($c.Exe -eq "py") {
            if (-not (Get-Command py -ErrorAction SilentlyContinue)) { continue }
        } elseif (-not (Test-Path $c.Exe)) {
            continue
        }
        try {
            & $c.Exe @($c.Args + @("-c", "import sys; assert sys.version_info >= (3, 10)")) 2>$null
            if ($LASTEXITCODE -eq 0) { return $c }
        } catch { continue }
    }
    throw "Python 3.10+ required. Install from https://www.python.org/downloads/ or run: winget install Python.Python.3.10"
}

function Invoke-Python {
    param($Spec, [string[]]$ScriptArgs)
    & $Spec.Exe @($Spec.Args + $ScriptArgs)
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $($Spec.Exe) $($Spec.Args -join ' ') $($ScriptArgs -join ' ')" }
}

function Invoke-ExternalCommand {
    param(
        [string]$Exe,
        [string[]]$Args,
        [string]$FailureMessage = "External command failed"
    )
    # pip and other native tools write resolver warnings to stderr; with $ErrorActionPreference=Stop
    # PowerShell treats those as terminating NativeCommandError even when exit code is 0.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Exe @Args 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw $FailureMessage }
    } finally {
        $ErrorActionPreference = $prev
    }
}

Write-Host "=== Project Infinity 1 - AAIS bootstrap ===" -ForegroundColor Cyan
Write-Host "Repo: $Root"

$py = Find-Python
Write-Host "Python: $($py.Label)"

$venv = Join-Path $Root ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"

if (-not $SkipInstall) {
    if (-not (Test-Path $venvPython)) {
        Write-Host "Creating virtual environment..."
        Invoke-Python $py @("-m", "venv", $venv)
    }
    # Some Windows Python installs create .venv without pip (ensurepip disabled).
    & $venvPython -m pip --version 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Bootstrapping pip in .venv (ensurepip)..."
        & $venvPython -m ensurepip --upgrade
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Recreating broken virtual environment..."
            Remove-Item -Recurse -Force $venv
            Invoke-Python $py @("-m", "venv", $venv)
            & $venvPython -m ensurepip --upgrade
            if ($LASTEXITCODE -ne 0) { throw "Could not bootstrap pip in .venv" }
        }
    }
    Write-Host "Installing AAIS package and dependencies (editable)..."
    Invoke-ExternalCommand -Exe $venvPython -Args @("-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools") -FailureMessage "pip upgrade failed"
    $extras = @("dev")
    if ($InstallReal -or $Preset -in @("production", "default")) {
        $extras += "real"
    }
    $extraSpec = ($extras | Select-Object -Unique) -join ","
    Invoke-ExternalCommand -Exe $venvPython -Args @("-m", "pip", "install", "-e", ".[$extraSpec]") -FailureMessage "pip install failed"
}

$runPy = if (Test-Path $venvPython) { $venvPython } else {
    if ($SkipInstall) { throw "Missing .venv - run without -SkipInstall" }
    $venvPython
}

if ($Preset -eq "production") {
    Write-Host "Production AI preflight (preset=production)..."
    & $runPy (Join-Path $Root "scripts\preflight_production_ai.py") --preset production
    if ($LASTEXITCODE -ne 0) { throw "Production AI preflight failed - set API keys in .env or install .[real] extras" }
}

if (-not (Test-Path $venvPython)) { throw "Missing .venv - run without -SkipInstall" }

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
    Write-Host "Created .env from .env.example (set provider keys in .env for frontier models)"
}

Write-Host "Preparing runtime data..."
& $runPy -m aais prepare --data-dir $DataDir
if ($LASTEXITCODE -ne 0) { throw "aais prepare failed" }
& $runPy -m aais doctor --data-dir $DataDir
if ($LASTEXITCODE -ne 0) { throw "aais doctor failed" }

$conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    if ($ReplaceExisting) {
        Write-Host "Stopping process on port $Port (PID $($conn.OwningProcess))..."
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    } else {
        Write-Host ""
        Write-Host "Port $Port is already in use (PID $($conn.OwningProcess))." -ForegroundColor Yellow
        Write-Host "  Option A: .\scripts\start-infinity1.ps1 -ReplaceExisting"
        Write-Host "  Option B: open http://127.0.0.1:$Port/health - server may already be running"
        exit 1
    }
}

Write-Host ""
Write-Host "Starting AAIS (preset=$Preset, no browser)..." -ForegroundColor Green
Write-Host "  Health:   http://127.0.0.1:$Port/health"
Write-Host "  App:      http://127.0.0.1:$Port/app"
Write-Host "  Jarvis:   http://127.0.0.1:$Port/app/jarvis"
Write-Host "  Operator: http://127.0.0.1:$Port/operator"
Write-Host ""
Write-Host "Press Ctrl+C to stop."
Write-Host ""

& $runPy -m aais start --data-dir $DataDir --preset $Preset --no-browser --port $Port
