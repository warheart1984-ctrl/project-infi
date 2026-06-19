# install_windows.ps1 - Windows system dependencies for Lawful Nova Shell
#Requires -Version 5.1
$ErrorActionPreference = "Continue"

function Write-Log { param([string]$Message) Write-Host "[windows] $Message" -ForegroundColor Blue }
function Write-Ok { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warn { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }

function Install-Winget {
    param([string]$Id, [string]$Label)
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id $Id -e --accept-source-agreements --accept-package-agreements --silent 2>$null
        if ($LASTEXITCODE -eq 0 -or (Get-Command $Label -ErrorAction SilentlyContinue)) {
            Write-Ok $Label
            return $true
        }
    }
    return $false
}

Write-Log "Installing core tools (winget preferred)..."

$packages = @(
    @{ Id = "Git.Git"; Label = "git" },
    @{ Id = "GitHub.cli"; Label = "gh" },
    @{ Id = "BurntSushi.ripgrep.MSVC"; Label = "rg" },
    @{ Id = "junegunn.fzf"; Label = "fzf" },
    @{ Id = "Python.Python.3.12"; Label = "python" },
    @{ Id = "OpenJS.NodeJS.LTS"; Label = "node" }
)

foreach ($pkg in $packages) {
    if (Get-Command $pkg.Label -ErrorAction SilentlyContinue) {
        Write-Ok "$($pkg.Label) (already installed)"
    } elseif (-not (Install-Winget -Id $pkg.Id -Label $pkg.Label)) {
        Write-Warn "$($pkg.Label) not installed - install manually or via winget: $($pkg.Id)"
    }
}

if (-not (Get-Command pwsh -ErrorAction SilentlyContinue)) {
    Install-Winget -Id "Microsoft.PowerShell" -Label "pwsh" | Out-Null
}

$nvmHome = Join-Path $env:USERPROFILE "nvm"
if (-not (Test-Path $nvmHome)) {
    Write-Warn "nvm-windows not detected. Install from: https://github.com/coreybutler/nvm-windows/releases"
    Write-Warn "After install, set NVM_HOME and NVM_SYMLINK in System Environment Variables."
} else {
    Write-Ok "nvm-windows found at $nvmHome"
}

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    $driver = (nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>$null | Select-Object -First 1)
    Write-Ok "NVIDIA driver: $driver"
} else {
    Write-Warn "nvidia-smi not found. Install NVIDIA drivers and CUDA 12+ for GPU acceleration."
    Write-Warn "https://developer.nvidia.com/cuda-downloads"
}

if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
    Install-Winget -Id "Microsoft.VisualStudioCode" -Label "code" | Out-Null
}

Write-Ok "Windows setup complete."
