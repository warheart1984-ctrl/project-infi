param(
    [switch]$UseAdapters
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $root

$runtimeDir = Join-Path $root ".runtime"
if (-not (Test-Path $runtimeDir)) {
    New-Item -ItemType Directory -Path $runtimeDir | Out-Null
}

$python = $null
$pythonw = $null
$pythonLauncher = $null
$pythonLauncherArgs = @()
$pythonPathEntries = @()
$pythonModeLabel = $null
$candidateEnvNames = @(".venv", ".venv-repair-backup-20260402")

foreach ($envName in $candidateEnvNames) {
    $candidateRoot = Join-Path $root $envName
    $candidatePython = Join-Path $candidateRoot "Scripts\python.exe"
    $candidateSitePackages = Join-Path $candidateRoot "Lib\site-packages"

    if ((Test-Path $candidateSitePackages) -and ($pythonPathEntries -notcontains $candidateSitePackages)) {
        $pythonPathEntries += $candidateSitePackages
    }

    if (-not (Test-Path $candidatePython)) {
        continue
    }

    try {
        & $candidatePython -c "import sys" *> $null
        $python = $candidatePython
        $candidatePythonw = Join-Path $candidateRoot "Scripts\pythonw.exe"
        if (Test-Path $candidatePythonw) {
            $pythonw = $candidatePythonw
        }
        $pythonModeLabel = $envName
        break
    } catch {
        continue
    }
}

if (-not $python) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
    $probePath = (@($pythonPathEntries) + @($env:PYTHONPATH) | Where-Object { $_ }) -join ';'
    if ($launcher -and $pythonPathEntries.Count -gt 0) {
        try {
            $previousPythonPath = $env:PYTHONPATH
            $env:PYTHONPATH = $probePath
            & $launcher -3.12 -c "import flask, dotenv, torch" *> $null
            $pythonLauncher = $launcher
            $pythonLauncherArgs = @("-3.12")
            $pythonModeLabel = "py -3.12 fallback"
        } catch {
            $pythonLauncher = $null
            $pythonLauncherArgs = @()
        } finally {
            $env:PYTHONPATH = $previousPythonPath
        }
    }
}

if (-not $python -and -not $pythonLauncher) {
    throw "Missing a working Python 3.12 runtime. Checked .venv, .venv-repair-backup-20260402, and py -3.12 fallback."
}

$env:ENVIRONMENT = "production"
$env:AAIS_PRIMARY_PROJECT = "AAIS-main"
$env:AAIS_LOG_FILE = Join-Path $runtimeDir "laptop-api.log"
$env:AAIS_ENABLE_TEXT_ADAPTERS = if ($UseAdapters) { "1" } else { "0" }
$env:FORGE_BASE_URL = "http://127.0.0.1:6060"
$env:FORGE_EVAL_BASE_URL = "http://127.0.0.1:6061"
$env:EVOLVE_BASE_URL = "http://127.0.0.1:6062"
$env:FORGE_PORT = "6060"
$env:FORGE_EVAL_PORT = "6061"
$env:EVOLVE_PORT = "6062"

Remove-Item Env:AAIS_TEXT_ADAPTER_PATH -ErrorAction SilentlyContinue
Remove-Item Env:AAIS_TEXT_ADAPTER_FAST_PATH -ErrorAction SilentlyContinue
Remove-Item Env:AAIS_TEXT_ADAPTER_THINK_PATH -ErrorAction SilentlyContinue

$fastAdapter = Join-Path $root "training\out\jarvis-fast-lora-1p5b\final"
$thinkAdapter = Join-Path $root "training\out\jarvis-think-lora-1p5b\final"
$legacyFastAdapter = Join-Path $root "training\out\jarvis-fast-lora\final"
$legacyThinkAdapter = Join-Path $root "training\out\jarvis-think-lora\final"
$singleAdapter = Join-Path $root "training\out\jarvis-qwen-lora\final"

if (-not (Test-Path $fastAdapter) -and (Test-Path $legacyFastAdapter)) {
    $fastAdapter = $legacyFastAdapter
}

if (-not (Test-Path $thinkAdapter) -and (Test-Path $legacyThinkAdapter)) {
    $thinkAdapter = $legacyThinkAdapter
}

if ($UseAdapters) {
    if (Test-Path $fastAdapter) {
        $env:AAIS_TEXT_ADAPTER_FAST_PATH = $fastAdapter
    }

    if (Test-Path $thinkAdapter) {
        $env:AAIS_TEXT_ADAPTER_THINK_PATH = $thinkAdapter
    }

    if ((-not (Test-Path $fastAdapter)) -and (-not (Test-Path $thinkAdapter)) -and (Test-Path $singleAdapter)) {
        $env:AAIS_TEXT_ADAPTER_PATH = $singleAdapter
    }
}

$servicePythonPath = (@($pythonPathEntries) + @($env:PYTHONPATH) | Where-Object { $_ }) -join ';'
$forgeScript = ".\\tools\\services\\start_forge.py"
$forgeEvalScript = ".\\tools\\services\\start_forge_eval.py"
$evolveScript = ".\\tools\\services\\start_evolve_engine.py"

$forgeConn = Get-NetTCPConnection -LocalPort 6060 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $forgeConn) {
    $previousPythonPath = $env:PYTHONPATH
    if ($pythonLauncher) {
        $env:PYTHONPATH = $servicePythonPath
        Start-Process -FilePath $pythonLauncher `
            -ArgumentList @($pythonLauncherArgs + @($forgeScript)) `
            -WorkingDirectory $root `
            -WindowStyle Hidden | Out-Null
    } elseif (Test-Path $pythonw) {
        Start-Process -FilePath $pythonw `
            -ArgumentList $forgeScript `
            -WorkingDirectory $root | Out-Null
    } else {
        Start-Process -FilePath $python `
            -ArgumentList $forgeScript `
            -WorkingDirectory $root `
            -RedirectStandardOutput (Join-Path $runtimeDir "forge.log") `
            -RedirectStandardError (Join-Path $runtimeDir "forge.err") | Out-Null
    }
    $env:PYTHONPATH = $previousPythonPath
}

$forgeEvalConn = Get-NetTCPConnection -LocalPort 6061 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $forgeEvalConn) {
    $previousPythonPath = $env:PYTHONPATH
    if ($pythonLauncher) {
        $env:PYTHONPATH = $servicePythonPath
        Start-Process -FilePath $pythonLauncher `
            -ArgumentList @($pythonLauncherArgs + @($forgeEvalScript)) `
            -WorkingDirectory $root `
            -WindowStyle Hidden | Out-Null
    } elseif (Test-Path $pythonw) {
        Start-Process -FilePath $pythonw `
            -ArgumentList $forgeEvalScript `
            -WorkingDirectory $root | Out-Null
    } else {
        Start-Process -FilePath $python `
            -ArgumentList $forgeEvalScript `
            -WorkingDirectory $root `
            -RedirectStandardOutput (Join-Path $runtimeDir "forge-eval.log") `
            -RedirectStandardError (Join-Path $runtimeDir "forge-eval.err") | Out-Null
    }
    $env:PYTHONPATH = $previousPythonPath
}

$evolveConn = Get-NetTCPConnection -LocalPort 6062 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $evolveConn) {
    $previousPythonPath = $env:PYTHONPATH
    if ($pythonLauncher) {
        $env:PYTHONPATH = $servicePythonPath
        Start-Process -FilePath $pythonLauncher `
            -ArgumentList @($pythonLauncherArgs + @($evolveScript)) `
            -WorkingDirectory $root `
            -WindowStyle Hidden | Out-Null
    } elseif (Test-Path $pythonw) {
        Start-Process -FilePath $pythonw `
            -ArgumentList $evolveScript `
            -WorkingDirectory $root | Out-Null
    } else {
        Start-Process -FilePath $python `
            -ArgumentList $evolveScript `
            -WorkingDirectory $root `
            -RedirectStandardOutput (Join-Path $runtimeDir "evolve-engine.log") `
            -RedirectStandardError (Join-Path $runtimeDir "evolve-engine.err") | Out-Null
    }
    $env:PYTHONPATH = $previousPythonPath
}

$backendConn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $backendConn) {
    $previousPythonPath = $env:PYTHONPATH
    if ($pythonLauncher) {
        $env:PYTHONPATH = (@($pythonPathEntries) + @($previousPythonPath) | Where-Object { $_ }) -join ';'
    }
    if ($pythonLauncher) {
        Start-Process -FilePath $pythonLauncher `
            -ArgumentList @($pythonLauncherArgs + @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000")) `
            -WorkingDirectory $root `
            -WindowStyle Hidden | Out-Null
    } elseif (Test-Path $pythonw) {
        # pythonw avoids Windows console-close crashes during long-running local inference.
        Start-Process -FilePath $pythonw `
            -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
            -WorkingDirectory $root | Out-Null
    } else {
        Start-Process -FilePath $python `
            -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
            -WorkingDirectory $root `
            -RedirectStandardOutput (Join-Path $runtimeDir "laptop-api.log") `
            -RedirectStandardError (Join-Path $runtimeDir "laptop-api.err") | Out-Null
    }
    $env:PYTHONPATH = $previousPythonPath
}

$env:VITE_API_URL = "http://127.0.0.1:8000"
$env:REACT_APP_API_URL = "http://127.0.0.1:8000"
$frontendConn = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $frontendConn) {
    Start-Process -FilePath "npm.cmd" `
        -ArgumentList "start" `
        -WorkingDirectory (Join-Path $root "frontend") `
        -RedirectStandardOutput (Join-Path $runtimeDir "frontend.log") `
        -RedirectStandardError (Join-Path $runtimeDir "frontend.err") | Out-Null
}

$healthUrl = "http://127.0.0.1:8000/health"
$prewarmUrl = "http://127.0.0.1:8000/legacy_api/api/system/prewarm"
$deadline = (Get-Date).AddMinutes(3)
$health = $null

while ((Get-Date) -lt $deadline) {
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 5
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}

if ($null -ne $health -and $health.ai_status -ne "initialized") {
    Write-Host "Prewarming Jarvis model..."
    try {
        $null = Invoke-RestMethod -Uri $prewarmUrl -Method Post -TimeoutSec 180
    } catch {
        Write-Warning "Jarvis prewarm did not complete: $($_.Exception.Message)"
    }
}

Write-Host "AAIS personal mode starting..."
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Forge:    http://127.0.0.1:6060/health"
Write-Host "Eval:     http://127.0.0.1:6061/health"
Write-Host "Evolve:   http://127.0.0.1:6062/health"
if ($UseAdapters) {
    if (Test-Path $fastAdapter) {
        Write-Host "Fast adapter: $fastAdapter"
    }
    if (Test-Path $thinkAdapter) {
        Write-Host "Think adapter: $thinkAdapter"
    }
    if ((-not (Test-Path $fastAdapter)) -and (-not (Test-Path $thinkAdapter)) -and (Test-Path $singleAdapter)) {
        Write-Host "Single adapter: $singleAdapter"
    }
} else {
    Write-Host "LLM:      Base Qwen 0.5B (laptop preset tuned for usable local latency)"
}
if ($pythonModeLabel) {
    Write-Host "Python:   $pythonModeLabel"
}
Write-Host "Logs:     $runtimeDir"
