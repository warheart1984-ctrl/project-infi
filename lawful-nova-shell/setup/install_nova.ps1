# install_nova.ps1 - Validates and wires the Nova LLM stack (Windows)
#Requires -Version 5.1
$ErrorActionPreference = "Continue"

function Write-Log { param([string]$Message) Write-Host "[nova] $Message" -ForegroundColor Blue }
function Write-Ok { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warn { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }

$NovarcPath = Join-Path $env:USERPROFILE ".novarc.ps1"
if (Test-Path $NovarcPath) { . $NovarcPath }

$NovaPort = if ($env:NOVA_PORT) { $env:NOVA_PORT } else { "8080" }
$NovaCli = if ($env:NOVA_CLI) { $env:NOVA_CLI } else { "nova" }
$NovaApiUrl = if ($env:NOVA_API_URL) { $env:NOVA_API_URL } else { "http://localhost:$NovaPort" }

Write-Log "Validating Nova LLM stack..."

if ($env:NOVA_VOSS_RUNTIME_PATH -and (Test-Path $env:NOVA_VOSS_RUNTIME_PATH)) {
    Write-Ok "Voss Runtime found: $($env:NOVA_VOSS_RUNTIME_PATH)"
    if ($env:Path -notlike "*$($env:NOVA_VOSS_RUNTIME_PATH)*") {
        $env:Path = "$($env:NOVA_VOSS_RUNTIME_PATH);$env:Path"
        Add-Content -Path $NovarcPath -Value "`$env:Path = `"$($env:NOVA_VOSS_RUNTIME_PATH);`$env:Path`"" -ErrorAction SilentlyContinue
    }
} else {
    Write-Warn "NOVA_VOSS_RUNTIME_PATH not set or not found."
    Write-Warn "Set it in $NovarcPath after your Nova stack is built."
}

if ($env:NOVA_CORTEX_PATH -and (Test-Path $env:NOVA_CORTEX_PATH)) {
    Write-Ok "Nova Cortex found: $($env:NOVA_CORTEX_PATH)"
} else {
    Write-Warn "NOVA_CORTEX_PATH not set or not found."
}

if (Get-Command $NovaCli -ErrorAction SilentlyContinue) {
    Write-Ok "Nova CLI reachable: $(Get-Command $NovaCli | Select-Object -ExpandProperty Source)"
} else {
    Write-Warn "Nova CLI ('$NovaCli') not found in PATH."
}

try {
    $null = Invoke-WebRequest -Uri "$NovaApiUrl/health" -UseBasicParsing -TimeoutSec 3
    Write-Ok "Nova API responding at $NovaApiUrl"
} catch {
    Write-Warn "Nova API not responding at $NovaApiUrl (is the stack running?)"
}

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    $gpuName = (nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1)
    $gpuMem = (nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>$null | Select-Object -First 1)
    Write-Ok "NVIDIA GPU: $gpuName ($gpuMem)"
} else {
    Write-Warn "nvidia-smi not found. GPU acceleration unavailable."
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$NovaDir = Join-Path $env:USERPROFILE ".nova"
New-Item -ItemType Directory -Force -Path $NovaDir | Out-Null
$StackSrc = Join-Path $RepoRoot "config\nova\nova-stack.json"
if (Test-Path $StackSrc) {
    Copy-Item $StackSrc (Join-Path $NovaDir "nova-stack.json") -Force
    Write-Ok "nova-stack.json deployed to $NovaDir"
}

Write-Log "Nova stack validation complete."
