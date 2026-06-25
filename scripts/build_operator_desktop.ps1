# Build operator surface (Svelte) and publish WebView2 desktop host.
# Optional: -BundlePython embeds python\ beside OperatorDesktop.exe (no system Python)
# Optional: -Package creates dist\OperatorDesktop-*-portable.zip
# Optional: -Installer runs Inno Setup (requires ISCC.exe on PATH)
param(
    [switch]$BundlePython,
    [switch]$Package,
    [switch]$Installer
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Surface = Join-Path $Root "operator-surface"
$Desktop = Join-Path $Root "desktop\webview2"
$Publish = Join-Path $Root "dist\operator-desktop"

Write-Host "Building operator-surface..."
Push-Location $Surface
if (-not (Test-Path "node_modules")) {
    npm install
}
npm run build
Pop-Location

Write-Host "Publishing WebView2 host..."
if (Test-Path $Publish) {
    Remove-Item -Recurse -Force $Publish
}
New-Item -ItemType Directory -Force -Path $Publish | Out-Null

dotnet publish $Desktop\OperatorHost.csproj -c Release -r win-x64 -o $Publish

$DistTarget = Join-Path $Publish "operator-surface\dist"
New-Item -ItemType Directory -Force -Path $DistTarget | Out-Null
Copy-Item -Recurse -Force (Join-Path $Surface "dist\*") $DistTarget

$ConfigTarget = Join-Path $Publish "operator_kernel.config.yaml"
Copy-Item -Force (Join-Path $Root "operator_kernel.config.yaml") $ConfigTarget
# Portable build: let launcher set AAIS_WORKSPACE_ROOT instead of dist folder.
(Get-Content $ConfigTarget -Raw) -replace '(?m)^workspace_root:\s*"\."\s*$', 'workspace_root: ""' |
    Set-Content -Path $ConfigTarget -Encoding UTF8 -NoNewline

$KernelPkg = Join-Path $Publish "operator_kernel"
if (Test-Path $KernelPkg) {
    Remove-Item -Recurse -Force $KernelPkg
}
Copy-Item -Recurse -Force (Join-Path $Root "operator_kernel") $KernelPkg

$NovaPkg = Join-Path $Publish "nova"
if (Test-Path $NovaPkg) {
    Remove-Item -Recurse -Force $NovaPkg
}
Copy-Item -Recurse -Force (Join-Path $Root "nova") $NovaPkg

$ConfigsTarget = Join-Path $Publish "configs"
if (Test-Path $ConfigsTarget) {
    Remove-Item -Recurse -Force $ConfigsTarget
}
Copy-Item -Recurse -Force (Join-Path $Root "configs") $ConfigsTarget

# Remove __pycache__ from published Python trees
Get-ChildItem -Path $Publish -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

$WorkspaceDir = Join-Path $Publish "workspace"
New-Item -ItemType Directory -Force -Path $WorkspaceDir | Out-Null
@"
Operator workspace folder
=======================

Agent tasks read and write files under this directory by default.
Set AAIS_WORKSPACE_ROOT to your full AAIS repo path to work on the real project.
"@ | Set-Content -Path (Join-Path $WorkspaceDir "README.txt") -Encoding UTF8

if ($BundlePython) {
    & (Join-Path $PSScriptRoot "bundle_operator_python.ps1") -DistRoot $Publish
}

Write-Host "Published to $Publish"
Write-Host "Run: $Publish\OperatorDesktop.exe"

if ($Package) {
    & (Join-Path $PSScriptRoot "package_operator_desktop.ps1")
}
if ($Installer) {
    & (Join-Path $PSScriptRoot "build_operator_installer.ps1")
}
