# Lawful Nova Agentic Shell - PowerShell profile
# Linked to $PROFILE by bootstrap.ps1

$NovaRepoRoot = $env:LAWFUL_NOVA_REPO_ROOT
if (-not $NovaRepoRoot) {
    $NovaRepoRoot = Split-Path $PSScriptRoot -Parent
}

$NovarcPath = Join-Path $env:USERPROFILE ".novarc.ps1"
if (Test-Path $NovarcPath) { . $NovarcPath }

if ($env:NOVA_VOSS_RUNTIME_PATH -and (Test-Path $env:NOVA_VOSS_RUNTIME_PATH)) {
    $env:Path = "$env:NOVA_VOSS_RUNTIME_PATH;$env:Path"
}
if ($env:NOVA_RSL_PATH -and (Test-Path $env:NOVA_RSL_PATH)) {
    $env:Path = "$env:NOVA_RSL_PATH;$env:Path"
}

$NvmHome = Join-Path $env:USERPROFILE ".nvm"
if (Test-Path (Join-Path $NvmHome "nvm.exe")) {
    $env:NVM_HOME = $NvmHome
    $env:NVM_SYMLINK = Join-Path $env:USERPROFILE "nodejs"
    $env:Path = "$env:NVM_SYMLINK;$env:NVM_HOME;$env:Path"
}

function global:nova-chat {
    $cmd = $env:NOVA_CLI
    if (-not $cmd) { $cmd = "nova" }
    & $cmd chat @args
}

function global:novr {
    Write-Host "[Nova] Reviewing staged changes..." -ForegroundColor Cyan
    git status
    git diff --cached
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Review these staged git changes. Identify any issues. Then write a conventional commit message and commit."
}

function global:novtest {
    Write-Host "[Nova] Running test suite..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Run all tests in this project. If any fail, identify the root cause and fix the source code. Re-run until all pass. Max 5 iterations."
}

function global:novpr {
    Write-Host "[Nova] Creating PR..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Compare this branch to main. Generate a conventional PR title and a detailed description (What, Why, How to test). Then run: gh pr create --title '<title>' --body '<body>'"
}

function global:novdoc {
    Write-Host "[Nova] Generating documentation..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Analyze all source files in the current directory. Generate comprehensive documentation and write it to README.md."
}

function global:novsec {
    Write-Host "[Nova] Running security audit..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Perform a thorough security audit of this codebase. Check for: hardcoded secrets, injection vulnerabilities, insecure dependencies, missing auth checks. Output a severity-ranked report."
}

function global:novrefactor {
    param([Parameter(Mandatory = $true)][string]$File)
    Write-Host "[Nova] Refactoring $File..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Refactor $File for improved readability, maintainability, and performance. Preserve all existing behavior and public API. Run tests after."
}

function global:novstack {
    Write-Host "[Nova] Stack Status" -ForegroundColor Cyan
    Write-Host "  API:     $($env:NOVA_API_URL)"
    $gpu = "N/A"
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        $gpu = (nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1)
    }
    Write-Host "  GPU:     $gpu"
    Write-Host "  Cortex:  $($env:NOVA_CORTEX_PATH)"
    Write-Host "  Voss:    $($env:NOVA_VOSS_RUNTIME_PATH)"
    Write-Host "  GoW cfg: $($env:NOVA_GOW_CONFIG)"
    $url = if ($env:NOVA_API_URL) { $env:NOVA_API_URL } else { "http://localhost:8080" }
    try {
        $null = Invoke-WebRequest -Uri "$url/health" -UseBasicParsing -TimeoutSec 3
        Write-Host "  Health:  OK - API responding" -ForegroundColor Green
    } catch {
        Write-Host "  Health:  FAIL - API not responding" -ForegroundColor Yellow
    }
}

function global:novcursor {
    $repo = $env:LAWFUL_NOVA_REPO_ROOT
    if (-not $repo) { $repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent }
    $script = Join-Path $repo "lawful-nova-shell\scripts\start-nova-for-cursor.ps1"
    if (-not (Test-Path $script)) {
        $script = Join-Path $repo "scripts\start-nova-for-cursor.ps1"
    }
    if (-not (Test-Path $script)) {
        Write-Host "[Nova] start-nova-for-cursor.ps1 not found. See lawful-nova-shell/CURSOR.md" -ForegroundColor Yellow
        return
    }
    & $script @args
}

function global:novverify {
    $repo = $env:LAWFUL_NOVA_REPO_ROOT
    if (-not $repo) { $repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent }
    $script = Join-Path $repo "lawful-nova-shell\scripts\verify-nova-local.ps1"
    if (-not (Test-Path $script)) {
        $script = Join-Path $repo "scripts\verify-nova-local.ps1"
    }
    if (-not (Test-Path $script)) {
        Write-Host "[Nova] verify-nova-local.ps1 not found. See lawful-nova-shell/CURSOR.md" -ForegroundColor Yellow
        return
    }
    & $script @args
}

Write-Host ""
Write-Host "[Nova] Lawful Nova shell ready (PowerShell)." -ForegroundColor Green
Write-Host "   nova-chat | novr | novtest | novpr | novdoc | novsec | novstack | novcursor | novverify"
Write-Host ""
