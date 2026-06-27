# bootstrap.ps1 - Lawful Nova Agentic Shell Bootstrap (Windows)
#Requires -Version 5.1
param(
    [switch]$NonInteractive
)
$ErrorActionPreference = "Stop"

if (-not $PSBoundParameters.ContainsKey('NonInteractive')) {
    try { $NonInteractive = [Console]::IsInputRedirected } catch { $NonInteractive = $false }
}

function Write-Log { param([string]$Message) Write-Host "[nova-bootstrap] $Message" -ForegroundColor Blue }
function Write-Ok { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warn { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Banner { param([string]$Title)
    Write-Host ""
    Write-Host "=======================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "=======================================" -ForegroundColor Cyan
    Write-Host ""
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

Write-Banner "Lawful Nova Agentic Shell Bootstrap (Windows)"
Write-Log "Repo root : $RepoRoot"
Write-Log "Date/Time : $(Get-Date)"

if (-not $IsWindows -and $env:OS -ne "Windows_NT") {
    Write-Error "Unsupported OS. Use setup/bootstrap.sh on macOS/Linux."
    exit 1
}

Write-Banner "Step 1/6 - System Dependencies"
& "$ScriptDir\install_windows.ps1"
Write-Ok "System dependencies ready."

Write-Banner "Step 2/6 - Node.js 20 and Python 3.12"
$nvmHome = Join-Path $env:USERPROFILE "nvm"
if (-not (Test-Path $nvmHome)) {
    Write-Warn "nvm-windows not found. Install from: https://github.com/coreybutler/nvm-windows/releases"
    Write-Warn "Then run: nvm install 20; nvm use 20"
} else {
    $env:NVM_HOME = $nvmHome
    $env:NVM_SYMLINK = Join-Path $env:USERPROFILE "nvm4w"
    $env:Path = "$env:NVM_HOME;$env:NVM_SYMLINK;$env:Path"
    nvm install 20 2>$null
    nvm use 20 2>$null
    if (Get-Command node -ErrorAction SilentlyContinue) {
        Write-Ok "Node.js $(node --version) ready."
    } else {
        Write-Warn "Node.js not in PATH after nvm setup."
    }
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3.12 --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Ok "Python $(py -3.12 --version) ready." }
    else { Write-Warn "Python 3.12 not found. Install from python.org or: winget install Python.Python.3.12" }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Ok "Python $(python --version) ready."
} else {
    Write-Warn "Python not found. Install 3.12+ from python.org or winget."
}

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.12 -m venv (Join-Path $RepoRoot ".venv")
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv (Join-Path $RepoRoot ".venv")
    }
}
if (Test-Path $VenvPython) {
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -e "$RepoRoot"
    Write-Ok "Local Lawful Nova package installed in .venv."
} else {
    Write-Warn "Could not create .venv; install Python 3.12+ and rerun bootstrap."
}

Write-Banner "Step 3/6 - Nova Stack Validation"
& "$ScriptDir\install_nova.ps1"
Write-Ok "Nova stack validated."

Write-Banner "Step 4/6 - Linking Config Files"
$NovarcDest = Join-Path $env:USERPROFILE ".novarc.ps1"
$NovarcSrc = Join-Path $RepoRoot "config\novarc.ps1"
if ((Test-Path $NovarcDest) -and -not (Test-Path "$NovarcDest.bak")) {
    Copy-Item $NovarcDest "$NovarcDest.bak" -Force
    Write-Warn "Backed up $NovarcDest"
}
Copy-Item $NovarcSrc $NovarcDest -Force
$env:LAWFUL_NOVA_REPO_ROOT = $RepoRoot
$repoLine = "`$env:LAWFUL_NOVA_REPO_ROOT = '$($RepoRoot -replace "'", "''")'"
$novarcContent = Get-Content $NovarcDest -Raw
if ($novarcContent -notmatch 'LAWFUL_NOVA_REPO_ROOT') {
    Add-Content -Path $NovarcDest -Value "`n$repoLine"
} else {
    ($novarcContent -replace '\$env:LAWFUL_NOVA_REPO_ROOT\s*=.*', $repoLine) | Set-Content $NovarcDest -Encoding UTF8
}
Write-Ok "Deployed: $NovarcDest"

$NovaDir = Join-Path $env:USERPROFILE ".nova"
New-Item -ItemType Directory -Force -Path $NovaDir | Out-Null
Copy-Item (Join-Path $RepoRoot "config\nova\nova-stack.json") (Join-Path $NovaDir "nova-stack.json") -Force
Write-Ok "Deployed: $NovaDir\nova-stack.json"

$ProfileSrc = Join-Path $RepoRoot "config\profile.ps1"
$ProfileDir = Split-Path -Parent $PROFILE
if (-not (Test-Path $ProfileDir)) { New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null }
if ((Test-Path $PROFILE) -and -not (Test-Path "$PROFILE.bak")) {
    Copy-Item $PROFILE "$PROFILE.bak" -Force
    Write-Warn "Backed up $PROFILE"
}
$ProfileMarker = "# >>> lawful-nova-shell >>>"
$ProfileContent = @"
$ProfileMarker
# Lawful Nova - load from repo (re-run bootstrap to refresh path)
. '$ProfileSrc'
# <<< lawful-nova-shell <<<
"@
if (Test-Path $PROFILE) {
    $existing = Get-Content $PROFILE -Raw
    if ($existing -notmatch [regex]::Escape($ProfileMarker)) {
        Add-Content -Path $PROFILE -Value "`n$ProfileContent"
    }
} else {
    Set-Content -Path $PROFILE -Value $ProfileContent -Encoding UTF8
}
Write-Ok "PowerShell profile wired: $PROFILE"

$GitConfig = Join-Path $env:USERPROFILE ".gitconfig"
if (-not (Test-Path $GitConfig)) {
    if ($NonInteractive) {
        Write-Warn "No ~/.gitconfig; skipping git identity (run bootstrap interactively or create manually)."
    } else {
        $GitName = Read-Host "Git name"
        $GitEmail = Read-Host "Git email"
        $template = Get-Content (Join-Path $RepoRoot "config\.gitconfig.template") -Raw
        $template = $template -replace '\{\{GIT_NAME\}\}', $GitName -replace '\{\{GIT_EMAIL\}\}', $GitEmail
        Set-Content -Path $GitConfig -Value $template -Encoding UTF8
        Write-Ok "~/.gitconfig created."
    }
}

Write-Banner "Step 5/6 - Nova Stack Paths"
function Set-NovaVar {
    param([string]$Name, [string]$Prompt, [string]$Default)
    $NovarcPath = Join-Path $env:USERPROFILE ".novarc.ps1"
    $lines = Get-Content $NovarcPath
    $prefix = '$env:' + $Name
    foreach ($line in $lines) {
        if ($line -like "$prefix=*") {
            $eq = $line.IndexOf('=')
            if ($eq -gt 0) {
                $rest = $line.Substring($eq + 1).Trim()
                if ($rest.Length -ge 2) {
                    $quote = $rest[0]
                    if (($quote -eq "'" -or $quote -eq '"') -and $rest.EndsWith($quote)) {
                        $current = $rest.Substring(1, $rest.Length - 2)
                        if (-not [string]::IsNullOrWhiteSpace($current)) {
                            Write-Ok "$Name already set."
                            return
                        }
                    }
                }
            }
        }
    }
    $val = $Default
    if (-not $NonInteractive) {
        $val = Read-Host "$Prompt [default: $Default]"
        if ([string]::IsNullOrWhiteSpace($val)) { $val = $Default }
    } else {
        Write-Log "$Prompt -> $val (default, non-interactive)"
    }
    $escaped = $val -replace "'", "''"
    $newLine = "`$env:$Name = '$escaped'"
    $filtered = @($lines | Where-Object { $_ -notlike "$prefix=*" })
    $filtered += $newLine
    Set-Content -Path $NovarcPath -Value ($filtered -join "`r`n") -Encoding UTF8
    Write-Ok "$Name set."
}

Set-NovaVar -Name "NOVA_PORT" -Prompt "Nova API port" -Default "8080"
Set-NovaVar -Name "NOVA_CLI" -Prompt "Nova CLI command" -Default (Join-Path $RepoRoot "bin\nova.ps1")
Set-NovaVar -Name "NOVA_VOSS_RUNTIME_PATH" -Prompt "Path to Voss Runtime" -Default (Join-Path $RepoRoot "nova")
Set-NovaVar -Name "NOVA_CORTEX_PATH" -Prompt "Path to Nova Cortex" -Default (Join-Path $RepoRoot "nova")
Set-NovaVar -Name "NOVA_GOW_CONFIG" -Prompt "Path to Gates of Wonder config" -Default (Join-Path $RepoRoot "config\nova\nova-stack.json")
Set-NovaVar -Name "NOVA_RSL_PATH" -Prompt "Path to RSL" -Default (Join-Path $RepoRoot "nova")
Set-NovaVar -Name "NOVA_GPU_DEVICE" -Prompt "NVIDIA GPU device index" -Default "0"
Set-NovaVar -Name "GITHUB_TOKEN" -Prompt "GitHub PAT (optional, leave blank)" -Default ""

Write-Banner "Step 6/6 - Verification"
& "$ScriptDir\verify.ps1"

Write-Host ""
Write-Host "Nova shell bootstrap complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Reload profile     : . `$PROFILE"
Write-Host "  Start Nova         : nova-chat"
Write-Host "  One-shot prompt    : nova run 'your task'"
Write-Host "  Diagnostics        : .\setup\verify.ps1 -Verbose"
Write-Host ""
