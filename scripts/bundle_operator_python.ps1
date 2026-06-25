#Requires -Version 5.1
<#
.SYNOPSIS
  Download Windows embeddable Python and install minimal operator_kernel deps into dist/operator-desktop/python/.
#>
param(
    [string]$PythonVersion = "3.12.7",
    [string]$DistRoot = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $DistRoot) {
    $DistRoot = Join-Path $RepoRoot "dist\operator-desktop"
}

$PythonDir = Join-Path $DistRoot "python"
$EmbedZip = "python-$PythonVersion-embed-amd64.zip"
$EmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/$EmbedZip"
$ReqFile = Join-Path $RepoRoot "requirements-operator-kernel.txt"

if ((Test-Path (Join-Path $PythonDir "python.exe")) -and -not $Force) {
    Write-Host "Bundled Python already present at $PythonDir (use -Force to rebuild)."
    exit 0
}

if (-not (Test-Path $ReqFile)) {
    throw "Missing requirements file: $ReqFile"
}

New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null
$TempDir = Join-Path $env:TEMP "operator-python-bundle-$PythonVersion"
$ZipPath = Join-Path $env:TEMP $EmbedZip

if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

Write-Host "Downloading $EmbedUrl ..."
Invoke-WebRequest -Uri $EmbedUrl -OutFile $ZipPath -UseBasicParsing
Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

# Enable site-packages in embeddable distro (uncomment import site).
$PthFiles = Get-ChildItem -Path $TempDir -Filter "python*._pth"
if ($PthFiles.Count -eq 0) {
    throw "Could not find python*._pth in embeddable zip"
}
$PthPath = $PthFiles[0].FullName
$pth = Get-Content $PthPath
$pth = $pth | ForEach-Object {
    if ($_ -match '^\s*#\s*import site\s*$') { 'import site' } else { $_ }
}
Set-Content -Path $PthPath -Value $pth -Encoding ASCII

$BundledPython = Join-Path $TempDir "python.exe"
if (-not (Test-Path $BundledPython)) {
    throw "python.exe not found after extract"
}

function Install-Pip {
    param([string]$PythonExe)
    Write-Host "Installing pip ..."
    & $PythonExe -m ensurepip --upgrade 2>$null
    if ($LASTEXITCODE -eq 0) { return }
    Write-Host "ensurepip unavailable; bootstrapping with get-pip.py ..."
    $GetPip = Join-Path $env:TEMP "get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip -UseBasicParsing
    & $PythonExe $GetPip --no-warn-script-location
    if ($LASTEXITCODE -ne 0) { throw "get-pip bootstrap failed with exit $LASTEXITCODE" }
}

Install-Pip -PythonExe $BundledPython

Write-Host "Installing operator_kernel dependencies ..."
& $BundledPython -m pip install --upgrade pip
& $BundledPython -m pip install -r $ReqFile
if ($LASTEXITCODE -ne 0) { throw "pip install failed with exit $LASTEXITCODE" }

& $BundledPython -c "import fastapi, uvicorn, httpx, pydantic, yaml; print('deps ok')"
if ($LASTEXITCODE -ne 0) { throw "post-install import check failed" }

if (Test-Path $PythonDir) { Remove-Item -Recurse -Force $PythonDir }
Move-Item -Path $TempDir -Destination $PythonDir

Write-Host "Bundled Python ready: $PythonDir"
Write-Host "  python.exe -c `"import fastapi, uvicorn; print('ok')`""
