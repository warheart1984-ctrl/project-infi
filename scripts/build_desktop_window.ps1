# Build AAIS desktop window executable (Windows) — pywebview shell.
# Output: dist\aais_desktop.exe (not committed to git)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "Installing desktop build dependencies..."
python -m pip install -q -e ".[dev,desktop]"

Write-Host "Preparing frontend bundle..."
python -m aais prepare --data-dir "$Root\.runtime\aais-data"

Write-Host "Running PyInstaller (desktop window)..."
python -m PyInstaller --onefile --name aais_desktop --clean run_aais_desktop.py `
  --hidden-import=uvicorn `
  --hidden-import=uvicorn.logging `
  --hidden-import=uvicorn.loops `
  --hidden-import=uvicorn.loops.auto `
  --hidden-import=uvicorn.protocols `
  --hidden-import=uvicorn.protocols.http `
  --hidden-import=uvicorn.protocols.http.auto `
  --hidden-import=uvicorn.lifespan `
  --hidden-import=uvicorn.lifespan.on `
  --hidden-import=webview

Write-Host ""
Write-Host "Done. Run: dist\aais_desktop.exe"
Write-Host "Place .env next to the exe if you use cloud AI keys."
Write-Host "Do NOT commit dist\ to GitHub."
