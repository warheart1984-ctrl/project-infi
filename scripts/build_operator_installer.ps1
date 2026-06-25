# Build desktop app then compile Inno Setup installer (requires ISCC.exe on PATH).
param(
    [string]$Version = "0.1.0",
    [switch]$BundlePython,
    [switch]$Package,
    [switch]$BuildNovaCli
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Iss = Join-Path $Root "installer\operator_setup.iss"

$desktopArgs = @()
if ($BundlePython) { $desktopArgs += "-BundlePython" }
if ($Package) { $desktopArgs += "-Package" }
& (Join-Path $Root "scripts\build_operator_desktop.ps1") @desktopArgs

if ($BuildNovaCli) {
    & (Join-Path $Root "scripts\build_nova_cli.ps1")
}

$Publish = Join-Path $Root "dist\operator-desktop"
$ConfigsTarget = Join-Path $Publish "configs"
if (Test-Path $ConfigsTarget) { Remove-Item -Recurse -Force $ConfigsTarget }
Copy-Item -Recurse -Force (Join-Path $Root "configs") $ConfigsTarget

$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $iscc) {
    $defaultIscc = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $defaultIscc) {
        Write-Error "Inno Setup not found. Install from https://jrsoftware.org/isinfo.php or add ISCC.exe to PATH."
    }
    $iscc = $defaultIscc
} else {
    $iscc = $iscc.Source
}

Write-Host "Compiling installer with $iscc ..."
& $iscc $Iss
Write-Host "Installer output: $(Join-Path $Root 'dist\OperatorDesktop-' + $Version + '-win-x64-setup.exe')"
