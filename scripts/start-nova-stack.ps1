# Start Lawful Nova LLM stack — Windows PowerShell.
param(
    [switch]$ApiOnly,
    [switch]$OperatorOnly,
    [switch]$WithAais,
    [ValidateSet("default", "laptop", "mock")]
    [string]$Preset = "mock"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPy) {
    $PyExe = $VenvPy
} else {
    $PyExe = (Get-Command python -ErrorAction Stop).Source
}

$env:LAWFUL_NOVA_REPO_ROOT = $Root
$env:PYTHONPATH = $Root
$env:NOVA_API_URL = if ($env:NOVA_API_URL) { $env:NOVA_API_URL } else { "http://127.0.0.1:8080" }

function Test-NovaHealth([string]$BaseUrl) {
    $candidates = @($BaseUrl)
    if ($BaseUrl -match 'localhost') {
        $candidates += ($BaseUrl -replace 'localhost', '127.0.0.1')
    }
    foreach ($candidate in $candidates) {
        try {
            $null = Invoke-RestMethod -Uri "$($candidate.TrimEnd('/'))/health" -TimeoutSec 2
            return $true
        } catch {
            continue
        }
    }
    return $false
}

function Start-NovaApi {
    if (Test-NovaHealth $env:NOVA_API_URL) {
        Write-Host "Nova API already up at $($env:NOVA_API_URL)"
        return
    }
    Write-Host "Starting Nova API on $($env:NOVA_API_URL) ..."
    Start-Process -FilePath $PyExe -ArgumentList @("-m", "nova.api") -WorkingDirectory $Root -WindowStyle Hidden
    Start-Sleep -Seconds 2
    if (-not (Test-NovaHealth $env:NOVA_API_URL)) {
        throw "Nova API failed to start"
    }
    Write-Host "  OK $($env:NOVA_API_URL)/health"
}

function Start-OperatorStack {
    $env:OPERATOR_KERNEL_CONFIG = if ($env:OPERATOR_KERNEL_CONFIG) { $env:OPERATOR_KERNEL_CONFIG } else { Join-Path $Root "operator_kernel.config.yaml" }
    $env:AAIS_SIGNING_SECRET = if ($env:AAIS_SIGNING_SECRET) { $env:AAIS_SIGNING_SECRET } else { "operator-kernel-dev-secret" }
    $env:AAIS_WORKSPACE_ROOT = if ($env:AAIS_WORKSPACE_ROOT) { $env:AAIS_WORKSPACE_ROOT } else { $Root }
    New-Item -ItemType Directory -Force -Path $env:AAIS_WORKSPACE_ROOT | Out-Null

    if (-not (Test-NovaHealth "http://127.0.0.1:8791")) {
        Write-Host "Starting lawful brain on 127.0.0.1:8791 ..."
        Start-Process -FilePath $PyExe -ArgumentList @("-m", "operator_kernel.lawful_brain") -WorkingDirectory $Root -WindowStyle Hidden
        Start-Sleep -Seconds 2
    }
    if (-not (Test-NovaHealth "http://127.0.0.1:8790")) {
        Write-Host "Starting operator kernel on 127.0.0.1:8790 ..."
        Start-Process -FilePath $PyExe -ArgumentList @("-m", "operator_kernel") -WorkingDirectory $Root -WindowStyle Hidden
        Start-Sleep -Seconds 2
    }
}

if ($OperatorOnly) {
    Start-OperatorStack
} elseif ($ApiOnly) {
    Start-NovaApi
} else {
    Start-NovaApi
    Start-OperatorStack
}

Write-Host ""
Write-Host "Lawful Nova stack running:"
Write-Host "  Nova API:         $($env:NOVA_API_URL)/health"
Write-Host "  Lawful brain:     http://127.0.0.1:8791/health"
Write-Host "  Operator kernel:  http://127.0.0.1:8790/health"
Write-Host ""
Write-Host "CLI: $(Join-Path $Root 'lawful-nova-shell\bin\nova.ps1') health --json"

if ($WithAais) {
    if ($Preset -eq "laptop") {
        & (Join-Path $Root "scripts\restart-aais.ps1") -Preset laptop -LocalReal
    } else {
        & (Join-Path $Root "scripts\restart-aais.ps1") -Preset $Preset
    }
}
