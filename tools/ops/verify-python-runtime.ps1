param(
    [switch]$RunApiTests
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Missing .venv\\Scripts\\python.exe. Rebuild the project venv with: py -3.12 -m venv .venv"
}

Write-Host "Verifying AAIS Python runtime..."
Write-Host "Runner: $python"

& $python -c "import sys; print('Executable:', sys.executable); print('Version:', sys.version.split()[0]); print('Prefix:', sys.prefix)"
& $python -m pip --version
& $python -m pip show pillow
& $python -c "from PIL import Image; print('Pillow:', Image.__version__)"

if ($RunApiTests) {
    Write-Host "Running tests/test_api.py..."
    & $python -m pytest -q .\tests\test_api.py
}
