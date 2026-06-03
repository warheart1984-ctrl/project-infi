# Build terminal-only AAIS desktop executable (Windows).
# Output: dist\aais_terminal.exe (not committed to git)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "Installing desktop build dependencies..."
python -m pip install -q -e ".[dev,desktop]"

Write-Host "Preparing frontend bundle..."
python -m aais prepare --data-dir "$Root\.runtime\aais-data"

Write-Host "Running PyInstaller (terminal)..."
python -m PyInstaller --onefile --name aais_terminal --clean run_aais.py `
  --hidden-import=uvicorn `
  --hidden-import=uvicorn.logging `
  --hidden-import=uvicorn.loops `
  --hidden-import=uvicorn.loops.auto `
  --hidden-import=uvicorn.protocols `
  --hidden-import=uvicorn.protocols.http `
  --hidden-import=uvicorn.protocols.http.auto `
  --hidden-import=uvicorn.lifespan `
  --hidden-import=uvicorn.lifespan.on

Write-Host ""
Write-Host "Done. Run: dist\aais_terminal.exe"
Write-Host "Place .env next to the exe if you use cloud AI keys."
Write-Host "Do NOT commit dist\ to GitHub."
