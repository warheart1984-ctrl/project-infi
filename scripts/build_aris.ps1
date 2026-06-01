# Build ARIS.exe (desktop launcher) with PyInstaller.
# Run from repo root: powershell -ExecutionPolicy Bypass -File scripts\build_aris.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Building ARIS desktop launcher..."
Write-Host "Repo: $(Get-Location)"
Write-Host ""

function Resolve-Python {
    if (Test-Path ".\.venv\Scripts\python.exe") { return ".\.venv\Scripts\python.exe" }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    return "py"
}

$py = Resolve-Python
& $py -m pip install -q -r requirements.txt pyinstaller

& $py -m PyInstaller ARIS.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$exe = Join-Path (Get-Location) "dist\ARIS.exe"
if (Test-Path $exe) {
    $size = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Built: $exe ($size MB)"
    Write-Host "Copy .env beside dist\ARIS.exe or set ARIS_WORKSPACE before launching."
} else {
    Write-Error "Build finished but dist\ARIS.exe was not found."
}
