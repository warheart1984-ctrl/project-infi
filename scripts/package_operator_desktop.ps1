# Zip dist\operator-desktop for portable distribution.
param(
    [string]$Version = "0.1.0"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Publish = Join-Path $Root "dist\operator-desktop"
$Dist = Join-Path $Root "dist"
$ZipName = "OperatorDesktop-$Version-win-x64-portable.zip"
$ZipPath = Join-Path $Dist $ZipName

if (-not (Test-Path (Join-Path $Publish "OperatorDesktop.exe"))) {
    Write-Error "Missing $Publish\OperatorDesktop.exe - run scripts\build_operator_desktop.ps1 first."
}

New-Item -ItemType Directory -Force -Path $Dist | Out-Null
if (Test-Path $ZipPath) {
    Remove-Item -Force $ZipPath
}

$readmeLines = @(
    "Operator Desktop (portable)",
    "========================",
    "",
    "1. Unzip anywhere (e.g. C:\Tools\OperatorDesktop)",
    "2. Double-click OperatorDesktop.exe",
    "",
    "The app starts Operator Kernel on http://127.0.0.1:8790 and Lawful Brain on :8791",
    "when they are not already running.",
    "",
    "Python:",
    "  - Place a Windows embeddable Python at python\python.exe next to the exe, OR",
    "  - Set OPERATOR_PYTHON to your python.exe, OR",
    "  - Install Python 3.11+ on PATH",
    "",
    "Workspace:",
    "  - Edits and agent tasks use the workspace\ folder next to the exe by default.",
    "  - Set AAIS_WORKSPACE_ROOT to point at your AAIS repo for full project access.",
    "",
    "Optional installer: run scripts\build_operator_installer.ps1 (requires Inno Setup 6)."
)
$readmePath = Join-Path $Publish "README-PORTABLE.txt"
Set-Content -Path $readmePath -Value $readmeLines -Encoding UTF8

Compress-Archive -Path (Join-Path $Publish "*") -DestinationPath $ZipPath -Force
Write-Host "Done. Portable package: $ZipPath"
