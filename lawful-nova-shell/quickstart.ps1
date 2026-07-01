# Quickstart Nova Desktop + governed Node backend from a fresh GitHub download.
#Requires -Version 5.1
param(
    [switch]$NoDesktop,
    [switch]$NoStart,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Desktop = Join-Path $Root "desktop"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

function Write-Step([string]$Message) { Write-Host "[quickstart] $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host "[OK] $Message" -ForegroundColor Green }

Set-Location $Root
Write-Step "Setting up governed Node backend from $Root"

if (-not (Test-Path $VenvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.12 -m venv (Join-Path $Root ".venv")
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv (Join-Path $Root ".venv")
    } else {
        throw "Python 3.10+ is required. Install Python 3.12 and rerun quickstart.ps1."
    }
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[dev]"
Write-Ok "Python backend installed"

if (Test-Path $Desktop) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "Node.js 20+ and npm are required for Nova Desktop."
    }
    Push-Location $Desktop
    npm install
    if (-not $SkipTests) {
        npm test
    }
    Pop-Location
    Write-Ok "Desktop dependencies installed"
}

if (-not $SkipTests) {
    & $VenvPython -m pytest tests -q
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "setup\verify.ps1")
}

if ($NoStart) {
    Write-Host ""
    Write-Host "Setup complete. Start manually:"
    Write-Host "  .\.venv\Scripts\python.exe -m nova.api"
    Write-Host "  cd desktop; npm start"
    exit 0
}

Write-Step "Starting governed Node backend: python -m nova.api"
$nodeProcess = Start-Process -FilePath $VenvPython -ArgumentList "-m", "nova.api" -WorkingDirectory $Root -PassThru
Start-Sleep -Seconds 3
Write-Ok "Node backend started as PID $($nodeProcess.Id)"
Write-Host "Node status: http://127.0.0.1:8080/node/status"

if (-not $NoDesktop -and (Test-Path $Desktop)) {
    Write-Step "Starting Nova Desktop"
    Push-Location $Desktop
    npm start
    Pop-Location
}
