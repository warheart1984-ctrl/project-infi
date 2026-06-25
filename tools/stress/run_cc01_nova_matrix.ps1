# CC-01 Nova matrix: 60s / 120s / 180s with fresh server per leg.
# Usage: .\tools\stress\run_cc01_nova_matrix.ps1 [-Preset mock|production]
param(
    [int]$Port = 8000,
    [string]$NovaBaseUrl = "http://127.0.0.1:8000",
    [string]$Preset = "mock",
    [int]$HealthWaitSec = 0,
    [switch]$UseStartInfinity1
)

$ErrorActionPreference = "Stop"
$Preset = $Preset.Trim().ToLower()
if ($Preset -notin @("mock", "default", "production", "laptop")) {
    throw "Invalid -Preset '$Preset'. Use mock, default, production, or laptop."
}
if ($HealthWaitSec -le 0) {
    $HealthWaitSec = if ($Preset -eq "mock") { 180 } else { 600 }
}
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$Harness = Join-Path $Root "tools\stress\cc01_controlled_collapse_harness.py"
$DataDir = Join-Path $Root ".runtime\aais-data"
$Runtime = Join-Path $Root ".runtime"
$LogDir = Join-Path $Runtime "cc01-$Preset-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Get-ListenerPids([int]$p) {
    @(Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { $_.OwningProcess }) | Select-Object -Unique
}

function Stop-MockOnPort {
    for ($attempt = 1; $attempt -le 8; $attempt++) {
        $conns = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
        if ($conns.Count -eq 0) {
            return
        }
        foreach ($conn in $conns) {
            Write-Host "Stopping PID $($conn.OwningProcess) on port $Port (attempt $attempt)..."
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    $left = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($left.Count -gt 0) {
        throw "Port $Port still in use (PIDs: $($left.OwningProcess -join ', '))"
    }
}

function Wait-Health {
    param(
        [System.Diagnostics.Process]$MockProc,
        [int]$MaxWaitSec = 180
    )
    $deadline = (Get-Date).AddSeconds($MaxWaitSec)
    while ((Get-Date) -lt $deadline) {
        if ($MockProc.HasExited) {
            throw "Mock process exited before health OK (exit=$($MockProc.ExitCode))"
        }
        try {
            $r = Invoke-WebRequest -Uri "$NovaBaseUrl/health" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) {
                Write-Host "Health OK at $NovaBaseUrl/health"
                return $true
            }
        } catch {}
        Start-Sleep -Seconds 1
    }
    throw "Health check failed after ${MaxWaitSec}s (mock pid=$($MockProc.Id), exited=$($MockProc.HasExited))"
}

function Start-AaisServer {
    Stop-MockOnPort
    $StartScript = Join-Path $Root "scripts\start-infinity1.ps1"
    if ($UseStartInfinity1 -and (Test-Path $StartScript)) {
        Write-Host "Starting AAIS via start-infinity1.ps1 (-SkipInstall -Preset $Preset -ReplaceExisting)..."
        $proc = Start-Process -FilePath "pwsh" `
            -ArgumentList @(
                "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $StartScript,
                "-SkipInstall", "-Preset", $Preset, "-ReplaceExisting", "-Port", "$Port", "-DataDir", $DataDir
            ) `
            -WorkingDirectory $Root `
            -PassThru `
            -WindowStyle Hidden
    } else {
        $legLog = if ($script:LegServerLog) { $script:LegServerLog } else { Join-Path $LogDir "server-latest.log" }
        Write-Host "Starting AAIS preset=$Preset on port $Port (log: $legLog)..."
        $startCmd = "cd /d `"$Root`" && `"$Py`" -m aais start --data-dir `"$DataDir`" --preset $Preset --no-browser --port $Port > `"$legLog`" 2>&1"
        $proc = Start-Process -FilePath "cmd.exe" `
            -ArgumentList @("/c", $startCmd) `
            -WorkingDirectory $Root `
            -PassThru `
            -WindowStyle Hidden
    }
    Wait-Health -MockProc $proc -MaxWaitSec $HealthWaitSec | Out-Null
    Wait-MockSteady -MockProc $proc | Out-Null
    $listeners = Get-ListenerPids $Port
    Write-Host "Listeners on port ${Port}: $($listeners -join ', ') (shell pid=$($proc.Id), preset=$Preset)"
    return $proc
}

function Show-MockLogTail {
    param([string]$LogPath, [int]$Lines = 40)
    if ($LogPath -and (Test-Path $LogPath)) {
        Write-Host "--- mock log tail ($LogPath) ---" -ForegroundColor Yellow
        Get-Content $LogPath -Tail $Lines -ErrorAction SilentlyContinue
    }
}

function Wait-MockSteady {
    param(
        [System.Diagnostics.Process]$MockProc,
        [int]$Polls = 3
    )
    for ($i = 1; $i -le $Polls; $i++) {
        if ($MockProc.HasExited) {
            throw "Mock process exited before steady wait (exit=$($MockProc.ExitCode), poll=$i/$Polls)"
        }
        try {
            $r = Invoke-WebRequest -Uri "$NovaBaseUrl/health" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -ne 200) {
                throw "Health poll $i/$Polls returned $($r.StatusCode)"
            }
        } catch {
            throw "Steady health poll $i/$Polls failed: $_"
        }
        if ($i -lt $Polls) { Start-Sleep -Seconds 1 }
    }
    Write-Host "Mock steady ($Polls health polls OK, pid=$($MockProc.Id))"
}

if (-not (Test-Path $Py)) { throw "Missing venv: $Py" }
if (-not (Test-Path (Join-Path $Root ".env"))) {
    Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
}

Write-Host "Preparing runtime data (once)..."
& $Py -m aais prepare --data-dir $DataDir
if ($LASTEXITCODE -ne 0) { throw "aais prepare failed" }
& $Py -m aais doctor --data-dir $DataDir
if ($LASTEXITCODE -ne 0) { throw "aais doctor failed" }

$matrixReport = @()
foreach ($dur in @(60, 120, 180)) {
    $outDir = Join-Path $Runtime "cc01-$Preset-${dur}s"
    $script:LegServerLog = Join-Path $LogDir "$Preset-${dur}s.log"
    Write-Host ""
    Write-Host "========== Leg ${dur}s (fresh server, preset=$Preset) ==========" -ForegroundColor Cyan

    $preListeners = Get-ListenerPids $Port
    if ($preListeners.Count -gt 0) {
        Write-Host "Clearing pre-existing listeners on port ${Port}: $($preListeners -join ', ')"
    }

    $mockProc = Start-AaisServer
    try {
        if ($mockProc.HasExited) {
            Show-MockLogTail -LogPath $script:LegServerLog
            throw "Server died between start and harness (exit=$($mockProc.ExitCode))"
        }
        & $Py $Harness `
            --backend nova `
            --threads 8 `
            --seed 42 `
            --max-qps 2 `
            --nova-base-url $NovaBaseUrl `
            --nova-queue-name cc01-chaos `
            --duration $dur `
            --out $outDir
        if ($LASTEXITCODE -ne 0) { throw "Harness exited $LASTEXITCODE for ${dur}s leg" }
        if ($mockProc.HasExited) {
            Show-MockLogTail -LogPath $script:LegServerLog
            throw "Server died during ${dur}s leg (exit=$($mockProc.ExitCode))"
        }

        $summaryPath = Join-Path $outDir "cc01_summary.json"
        if (Test-Path $summaryPath) {
            $summary = Get-Content $summaryPath -Raw | ConvertFrom-Json
            $matrixReport += [PSCustomObject]@{
                duration_sec = $dur
                would_pass   = $summary.would_pass
                failures     = ($summary.failure_counts | ConvertTo-Json -Compress)
                violations   = ($summary.violations -join ", ")
                out_dir      = $outDir
                mock_log     = $script:LegServerLog
            }
            Write-Host "Leg ${dur}s: would_pass=$($summary.would_pass) failures=$($summary.failure_counts | ConvertTo-Json -Compress)"
        }
    } finally {
        Write-Host "Stopping server after ${dur}s leg..."
        Stop-MockOnPort
        if ($mockProc -and -not $mockProc.HasExited) {
            Stop-Process -Id $mockProc.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
}

Write-Host ""
Write-Host "========== Matrix summary ==========" -ForegroundColor Green
$matrixReport | Format-Table -AutoSize
$reportPath = Join-Path $Runtime "cc01-$Preset-matrix-report.json"
$matrixReport | ConvertTo-Json -Depth 6 | Set-Content $reportPath -Encoding utf8
Write-Host "Wrote $reportPath"
