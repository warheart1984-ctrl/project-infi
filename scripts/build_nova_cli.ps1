# Build nova.exe with PyInstaller into dist/operator-desktop/
param(
    [string]$DistRoot = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $DistRoot) {
    $DistRoot = Join-Path $Root "dist\operator-desktop"
}

$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    $VenvPy = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $VenvPy) {
    throw "Python not found. Create .venv or add python to PATH."
}

& $VenvPy -m pip install pyinstaller --quiet
New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null

Push-Location $Root
& $VenvPy -m PyInstaller nova.spec --distpath $DistRoot --workpath (Join-Path $Root "build\nova-pyinstaller") --noconfirm
Pop-Location

$NovaExe = Join-Path $DistRoot "nova.exe"
if (-not (Test-Path $NovaExe)) {
    throw "PyInstaller did not produce $NovaExe"
}
Write-Host "Built $NovaExe"
