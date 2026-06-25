# Bootstrap WSL for CORI Docker workflows (Debian default).
# Run from PowerShell:  e:\project-infi\scripts\wsl_bootstrap.ps1

$ErrorActionPreference = "Stop"
$WslDistro = if ($env:WSL_DISTRO) { $env:WSL_DISTRO } else { "Debian" }

Write-Host "=== WSL bootstrap ($WslDistro) ==="

# Ensure legacy manager is running (helps some 0x80072747 socket errors)
try {
    if ((Get-Service LxssManager -ErrorAction SilentlyContinue).Status -ne "Running") {
        Start-Service LxssManager -ErrorAction SilentlyContinue
        Set-Service LxssManager -StartupType Automatic -ErrorAction SilentlyContinue
    }
} catch {
    Write-Host "(LxssManager: skipped - may need admin)"
}

# Warm distro (first start after reboot can take minutes)
Write-Host "Starting WSL distro..."
$warm = wsl -d $WslDistro -- echo "WSL OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "WSL failed: $warm"
}
Write-Host $warm

# Verify Docker inside WSL
Write-Host "Checking Docker in WSL..."
$dockerCheck = wsl -d $WslDistro -- bash -lc 'docker version --format "{{.Server.Version}}" 2>/dev/null || echo FAIL'
if ($dockerCheck -eq "FAIL" -or [string]::IsNullOrWhiteSpace($dockerCheck)) {
    Write-Host ""
    Write-Host "Docker not available in WSL. Enable one of:"
    Write-Host "  1. Docker Desktop -> Settings -> Resources -> WSL Integration -> $WslDistro"
    Write-Host "  2. Native dockerd in WSL: sudo service docker start"
    exit 1
}
Write-Host "Docker OK (server $dockerCheck)"

# Optional: python3-venv for a proper venv (otherwise pip --user is used)
$venvPkg = wsl -d $WslDistro -- bash -lc "python3 -m venv /tmp/_venv_test 2>&1" 2>&1
if ($venvPkg -match "python3-venv") {
    Write-Host ""
    Write-Host "Tip: for a clean venv, run once in WSL (needs sudo password):"
    Write-Host "  wsl -d $WslDistro"
    Write-Host "  sudo apt install -y python3-venv"
}

Write-Host ""
Write-Host "WSL is ready. Run HTTP proof:"
Write-Host "  e:\project-infi\scripts\wsl_ci_http_proof.ps1"
