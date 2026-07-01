# Verify Lawful Nova local slice — Windows PowerShell.
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ShellRoot = Split-Path -Parent $ScriptDir
$ParentRoot = Split-Path -Parent $ShellRoot
$RepoRoot = if ($env:LAWFUL_NOVA_REPO_ROOT) {
    $env:LAWFUL_NOVA_REPO_ROOT
} elseif ((Test-Path (Join-Path $ShellRoot "pyproject.toml")) -and (Test-Path (Join-Path $ShellRoot "nova"))) {
    $ShellRoot
} else {
    $ParentRoot
}

$Warn = 0
$Fail = 0

function Write-Ok([string]$Message) { Write-Host "[OK] $Message" }
function Write-Info([string]$Message) { Write-Host "[INFO] $Message" }
function Write-Warn([string]$Message) { Write-Host "[WARN] $Message"; $script:Warn++ }
function Write-Fail([string]$Message) { Write-Host "[FAIL] $Message"; $script:Fail++ }

Write-Host "=== Lawful Nova verify (windows) ==="
Write-Host "Repo: $RepoRoot"

$VenvCandidates = @(
    (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
    (Join-Path $ParentRoot ".venv\Scripts\python.exe")
)
$VenvPy = $VenvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($VenvPy -and (Test-Path $VenvPy)) {
    $PyExe = $VenvPy
    Write-Ok "Python .venv $PyExe"
} else {
    Write-Fail "Missing repo .venv at $VenvPy"
    $PyExe = $null
}

$CortexPath = if ($env:NOVA_CORTEX_PATH) { $env:NOVA_CORTEX_PATH } else { Join-Path $ShellRoot "nova" }
$VossPath = if ($env:NOVA_VOSS_RUNTIME_PATH) { $env:NOVA_VOSS_RUNTIME_PATH } else { Join-Path $ShellRoot "nova" }
$RslPath = if ($env:NOVA_RSL_PATH) { $env:NOVA_RSL_PATH } else { Join-Path $RepoRoot "governance" }

if (Test-Path $CortexPath) { Write-Ok "Cortex path $CortexPath" } else { Write-Fail "Missing cortex path $CortexPath" }
if (Test-Path $VossPath) { Write-Ok "Voss path $VossPath" } else { Write-Fail "Missing voss path $VossPath" }
if (Test-Path $RslPath) { Write-Ok "RSL path $RslPath" } else { Write-Warn "RSL path not found $RslPath" }

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Ok "Docker available"
} else {
    Write-Info "Docker not found - optional for native Windows agent"
}

$ApiUrl = if ($env:NOVA_API_URL) { $env:NOVA_API_URL } else { "http://127.0.0.1:8080" }
try {
    $null = Invoke-RestMethod -Uri "$($ApiUrl.TrimEnd('/'))/health" -TimeoutSec 2
    Write-Ok "Nova API $ApiUrl/health"
} catch {
    Write-Warn "Nova API not reachable at $ApiUrl (start: scripts/start-nova-stack.ps1 -ApiOnly)"
}

if ($PyExe) {
    $env:LAWFUL_NOVA_REPO_ROOT = $RepoRoot
    $env:PYTHONPATH = "$ShellRoot;$RepoRoot"
    $health = & $PyExe -m nova.cli health --json 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Direct LawfulLLM in-process"
    } else {
        Write-Fail "nova.cli health failed: $health"
    }
}

if ($Fail -gt 0) {
    Write-Host "Verify failed ($Fail critical, $Warn warnings)"
    exit 1
}

Write-Host "Verify passed ($Warn warnings)"
exit 0
