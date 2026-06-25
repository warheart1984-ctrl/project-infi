# Build double-click AAIS server executable (Windows).
# Output: dist\aais_terminal.exe
# Usage: .\scripts\build_aais_exe.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "Installing build dependencies..."
& $Python -m pip install -q -e ".[dev,desktop]"

Write-Host "Preparing frontend bundle..."
& $Python -m aais prepare --data-dir "$Root\.runtime\aais-data"

Write-Host "Running PyInstaller..."
$addData = @(
  "app;app",
  "src;src",
  "deploy;deploy",
  "governance;governance",
  "pyproject.toml;."
)
$addArgs = $addData | ForEach-Object { "--add-data", $_ }

& $Python -m PyInstaller --onefile --name aais_terminal --clean run_aais.py `
  @addArgs `
  --hidden-import=uvicorn `
  --hidden-import=uvicorn.logging `
  --hidden-import=uvicorn.loops `
  --hidden-import=uvicorn.loops.auto `
  --hidden-import=uvicorn.protocols `
  --hidden-import=uvicorn.protocols.http `
  --hidden-import=uvicorn.protocols.http.auto `
  --hidden-import=uvicorn.lifespan `
  --hidden-import=uvicorn.lifespan.on `
  --hidden-import=app.main `
  --hidden-import=src.api `
  --hidden-import=src.main `
  --hidden-import=fastapi `
  --hidden-import=starlette `
  --hidden-import=starlette.routing `
  --hidden-import=starlette.middleware `
  --hidden-import=starlette.staticfiles `
  --hidden-import=pydantic `
  --hidden-import=httpx

$readme = @"
AAIS Production Launcher (aais_terminal.exe)
==========================================

Double-click to start the AAIS server with the production preset:
  - Real AI mode (no mock fallback)
  - Mesh gossip OFF (no probes to ports 5000/5001)
  - Default URL: http://127.0.0.1:8000/health

First run:
  1. Place a .env file next to this exe if you use cloud API keys.
  2. First boot may download the lite local model (~1GB) — allow several minutes.
  3. Data is stored in .runtime\aais-data next to the exe.

Optional environment (system or .env):
  JARVIS_DATA_DIR=path\to\data
  AAIS_MODEL_MODE=local
  AAIS_LOCAL_MODEL=Qwen/Qwen2.5-0.5B-Instruct

Do not commit dist\ to git.
"@
$readme | Set-Content -Encoding UTF8 (Join-Path $Root "dist\AAIS_TERMINAL_README.txt")

$bat = @"
@echo off
cd /d "%~dp0"
echo Starting AAIS (production)...
aais_terminal.exe
if errorlevel 1 (
  echo.
  echo Server exited with an error. See messages above.
  pause
)
"@
$bat | Set-Content -Encoding ASCII (Join-Path $Root "dist\Start-AAIS.bat")

Write-Host ""
Write-Host "Done."
Write-Host "  Executable: dist\aais_terminal.exe"
Write-Host "  Launcher:   dist\Start-AAIS.bat"
Write-Host "  Readme:     dist\AAIS_TERMINAL_README.txt"
