# Run CORI HTTP cross-container proof using Docker in WSL.
# Requires: WSL2 with Docker (Docker Desktop WSL integration or native dockerd).

param(
    [switch]$TearDown
)

$ErrorActionPreference = "Stop"

$WslDistro = if ($env:WSL_DISTRO) { $env:WSL_DISTRO } else { "Debian" }

function Get-WslProjectPath {
    param([string]$WindowsPath)
    if ($WindowsPath -match '^([A-Za-z]):\\(.*)$') {
        $drive = $Matches[1].ToLower()
        $rest = ($Matches[2] -replace '\\', '/')
        return "/mnt/$drive/$rest"
    }
    throw "Cannot map path to WSL: $WindowsPath"
}

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$WslRoot = Get-WslProjectPath $ProjectRoot

if ($TearDown) {
    Write-Host "Tearing down CORI CI stack in WSL ($WslDistro)..."
    wsl -d $WslDistro bash -lc "cd '$WslRoot' && ./scripts/docker_compose.sh -f docker-compose.ci.yml -f docker-compose.ci-wsl.yml down -v"
    exit $LASTEXITCODE
}

Write-Host "Warming WSL distro: $WslDistro"
wsl -d $WslDistro -- echo "WSL ready" | Out-Null

Write-Host "Running HTTP stack proof in WSL at $WslRoot"
wsl -d $WslDistro bash -lc "cd '$WslRoot' && bash scripts/wsl_ci_http_proof.sh"
exit $LASTEXITCODE
