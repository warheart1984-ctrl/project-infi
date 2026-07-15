#Requires -Version 5.1
param(
    [switch]$ApiOnly
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
$ShellRoot = Join-Path $Root "lawful-nova-shell"

if (-not (Test-Path $ShellRoot)) {
    throw "Missing lawful-nova-shell at $ShellRoot"
}

$PythonCandidates = @(
    (Join-Path $ShellRoot ".venv\Scripts\python.exe"),
    (Join-Path $Root ".venv\Scripts\python.exe")
)
if ($env:OPERATOR_PYTHON) {
    $PythonCandidates += $env:OPERATOR_PYTHON
}
$PyExe = $PythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $PyExe) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $PyExe = $PythonCommand.Source
    }
}
if (-not $PyExe) {
    throw "Python 3.10+ or lawful-nova-shell .venv is required."
}

function Get-FreeNovaPort {
    param([int[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if (Test-NovaPortAvailable -Port $candidate) {
            return $candidate
        }
    }

    return $Candidates[0]
}

function Test-NovaPortAvailable {
    param([int]$Port)

    try {
        $matches = netstat -ano -p TCP 2>$null | Select-String -Pattern ":\s*$Port\s"
        return (-not $matches)
    } catch {
        return $true
    }
}

$env:LAWFUL_NOVA_REPO_ROOT = $Root
$preferredPort = if ($env:NOVA_PORT) { [int]$env:NOVA_PORT } else { 8080 }
$env:NOVA_PORT = if (Test-NovaPortAvailable -Port $preferredPort) {
    "$preferredPort"
} else {
    (Get-FreeNovaPort -Candidates @(8080, 8081, 8082)).ToString()
}
$env:NOVA_API_URL = "http://127.0.0.1:$($env:NOVA_PORT)"
$env:PYTHONPATH = if ($env:PYTHONPATH) {
    "$ShellRoot;$Root;$($env:PYTHONPATH)"
} else {
    "$ShellRoot;$Root"
}

function Test-NovaHealth {
    try {
        $null = Invoke-RestMethod -Uri "$($env:NOVA_API_URL.TrimEnd('/'))/health" -TimeoutSec 2
        return $true
    } catch {
        return $false
    }
}

if (Test-NovaHealth) {
    Write-Host "[Nova] API already reachable at $($env:NOVA_API_URL)/health"
    exit 0
}

Write-Host "[Nova] Starting Nova API at $($env:NOVA_API_URL)"
$null = Start-Process `
    -FilePath $PyExe `
    -ArgumentList "-m", "nova.api" `
    -WorkingDirectory $ShellRoot `
    -WindowStyle Hidden `
    -PassThru

$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    if (Test-NovaHealth) {
        $ready = $true
        break
    }
}

if (-not $ready) {
    throw "Nova API did not become healthy at $($env:NOVA_API_URL)/health"
}

Write-Host "[Nova] API ready at $($env:NOVA_API_URL)/health"

if ($ApiOnly) {
    exit 0
}

$Desktop = Join-Path $ShellRoot "desktop"
if ((Test-Path (Join-Path $Desktop "package.json")) -and (Get-Command npm -ErrorAction SilentlyContinue)) {
    Push-Location $Desktop
    try {
        npm start
    } finally {
        Pop-Location
    }
} else {
    Write-Host "[Nova] Desktop not started. Run `cd $Desktop; npm start` if you want the UI."
}
