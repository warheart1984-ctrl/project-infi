#Requires -Version 5.1
<#
.SYNOPSIS
  Inspect E:\ drive + canonical repo for production readiness (no guessing).

.DESCRIPTION
  Emits PASS/WARN/FAIL for ports, HTTP health, Nova verify, plug registry,
  worktree drift, hygiene, and unlawful-agent posture. Exit 1 on any FAIL.

.EXAMPLE
  .\scripts\e_drive_production_audit.ps1
  .\scripts\e_drive_production_audit.ps1 -JsonOut E:\project-infi\.runtime\e_drive_audit.json
#>
param(
    [string]$RepoRoot = "E:\project-infi",
    [string]$JsonOut = "",
    [switch]$SkipSizeScan
)

$ErrorActionPreference = "Continue"
$RepoRoot = (Resolve-Path $RepoRoot).Path

$novarcPath = Join-Path $env:USERPROFILE ".novarc.ps1"
if (Test-Path $novarcPath) {
    . $novarcPath
}
$env:LAWFUL_NOVA_REPO_ROOT = $RepoRoot

$Py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

$results = [ordered]@{
    audit_version = "e_drive_production_audit.v1"
    completed_at  = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    repo_root     = $RepoRoot
    checks        = @()
}
$fails = 0
$warns = 0

function Add-Check {
    param([string]$Id, [string]$Status, [string]$Detail)
    $script:results.checks += [ordered]@{ id = $Id; status = $Status; detail = $Detail }
    switch ($Status) {
        "FAIL" { $script:fails++ }
        "WARN" { $script:warns++ }
    }
}

function Test-Http {
    param([string]$Url, [int]$TimeoutSec = 5)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
        return @{ ok = $true; code = $r.StatusCode; body = $r.Content }
    } catch {
        return @{ ok = $false; code = 0; body = $_.Exception.Message }
    }
}

Write-Host "=== E: Drive Production Audit ===" -ForegroundColor Cyan
Write-Host "Canonical repo: $RepoRoot`n"

# --- Canonical repo ---
if (Test-Path $Py) {
    Add-Check "venv" "PASS" $Py
} else {
    Add-Check "venv" "FAIL" "Missing .venv - run .\scripts\start-infinity1.ps1"
}

$novarc = $novarcPath
if (Test-Path $novarc) {
    $rsl = $env:NOVA_RSL_PATH
    if ($rsl -like "*\governance") {
        Add-Check "novarc_rsl" "PASS" "NOVA_RSL_PATH=$rsl"
    } elseif ($rsl) {
        Add-Check "novarc_rsl" "WARN" "NOVA_RSL_PATH should end with \governance (got $rsl). Re-open shell after .novarc.ps1 fix."
    } else {
        Add-Check "novarc_rsl" "WARN" "NOVA_RSL_PATH unset - dot-source $novarc"
    }
} else {
    Add-Check "novarc" "WARN" "Missing $novarc - run lawful-nova-shell\setup\bootstrap.ps1"
}

# --- Ports ---
$portMap = @{
    8080 = "nova_api"
    8000 = "aais"
    3000 = "frontend_or_proxy"
    8790 = "operator_kernel"
    8791 = "lawful_brain"
    5000 = "megatron_optional"
}
foreach ($port in $portMap.Keys | Sort-Object) {
    $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    $name = $portMap[$port]
    if ($c) {
        $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        Add-Check "port_$port" "PASS" "$name listening pid=$($c.OwningProcess) $($proc.ProcessName)"
    } elseif ($port -in 8080, 8000) {
        Add-Check "port_$port" "FAIL" "$name not listening - required for daily ops"
    } elseif ($port -in 8790, 8791) {
        Add-Check "port_$port" "WARN" "$name not listening - run .\scripts\start-nova-stack.ps1"
    } else {
        Add-Check "port_$port" "PASS" "$name free (optional)"
    }
}

# --- HTTP health ---
$healthUrls = @(
    @{ id = "nova_health"; url = "http://127.0.0.1:8080/health"; required = $true },
    @{ id = "aais_health"; url = "http://127.0.0.1:8000/health"; required = $true },
    @{ id = "operator_health"; url = "http://127.0.0.1:8790/health"; required = $false },
    @{ id = "brain_health"; url = "http://127.0.0.1:8791/health"; required = $false }
)
foreach ($h in $healthUrls) {
    $t = Test-Http $h.url
    if ($t.ok) {
        Add-Check $h.id "PASS" "$($h.url) HTTP $($t.code)"
    } elseif ($h.required) {
        Add-Check $h.id "FAIL" "$($h.url) - $($t.body)"
    } else {
        Add-Check $h.id "WARN" "$($h.url) - $($t.body)"
    }
}

# --- AAIS contractor deps ---
try {
    $aais = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 5
    $down = @($aais.contractors | Where-Object { -not $_.reachable })
    if ($aais.mock_mode_active) {
        Add-Check "aais_mode" "PASS" "mock_mode_active=true (expected for local dev)"
    }
    if ($down.Count -gt 0) {
        $names = ($down | ForEach-Object { $_.name }) -join ", "
        Add-Check "aais_contractors" "WARN" "Unreachable optional contractors: $names (ports 6060-6062)"
    } else {
        Add-Check "aais_contractors" "PASS" "All contractors reachable"
    }
} catch {
    Add-Check "aais_mode" "WARN" "Could not parse AAIS health"
}

# --- Nova verify + productization ---
$verify = Join-Path $RepoRoot "lawful-nova-shell\setup\verify.ps1"
if (Test-Path $verify) {
    $env:LAWFUL_NOVA_REPO_ROOT = $RepoRoot
    & powershell -NoProfile -ExecutionPolicy Bypass -File $verify 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Add-Check "nova_verify" "PASS" "lawful-nova-shell\setup\verify.ps1"
    } else {
        Add-Check "nova_verify" "FAIL" "verify.ps1 exit $LASTEXITCODE"
    }
}

$gate = Join-Path $RepoRoot "scripts\nova_productization_gate.py"
if (Test-Path $gate) {
    $gateJson = & $Py $gate 2>&1 | Out-String
    try {
        $g = $gateJson | ConvertFrom-Json
        if ($g.local_lawful_slice_ready) {
            Add-Check "nova_productization" "PASS" "local_lawful_slice_ready=true"
        } else {
            Add-Check "nova_productization" "FAIL" "local_lawful_slice_ready=false"
        }
        if (-not $g.local_services_ready) {
            Add-Check "nova_full_stack" "WARN" "local_services_ready=false - run .\scripts\start-nova-stack.ps1"
        } else {
            Add-Check "nova_full_stack" "PASS" "local_services_ready=true"
        }
    } catch {
        Add-Check "nova_productization" "WARN" "Could not parse gate output"
    }
}

# --- Unlawful agents ---
$disableScript = Join-Path $RepoRoot "scripts\disable_unlawful_agents.py"
if (Test-Path $disableScript) {
    $dj = & $Py $disableScript --dry-run 2>&1 | Out-String
    try {
        $d = $dj | ConvertFrom-Json
        $enabledUnlawful = @($d.disabled_now | Where-Object { $_ })
        if ($enabledUnlawful.Count -eq 0) {
            $uaDetail = "{0} unlawful plugs off, {1} native plugs unchanged" -f $d.totals.already_off, $d.totals.lawful_unchanged
            Add-Check "unlawful_agents" "PASS" $uaDetail
        } else {
            Add-Check "unlawful_agents" "FAIL" "Still enabled: $($enabledUnlawful -join ', ')"
        }
    } catch {
        Add-Check "unlawful_agents" "WARN" "Could not parse disable_unlawful_agents output"
    }
}

# --- Repo hygiene ---
$hygiene = Join-Path $RepoRoot ".github\scripts\check-repo-hygiene.py"
if (Test-Path $hygiene) {
    $hout = & $Py $hygiene --repo-root $RepoRoot 2>&1 | Out-String
    $hflat = ($hout.Trim() -replace "`r?`n", ' | ')
    if ($LASTEXITCODE -ne 0) {
        Add-Check "repo_hygiene" "FAIL" $hflat
    } elseif ($hout -match 'warnings=(\d+)' -and [int]$Matches[1] -gt 0) {
        Add-Check "repo_hygiene" "WARN" $hflat
    } else {
        Add-Check "repo_hygiene" "PASS" "clean"
    }
}

# --- Git worktrees (drift) ---
try {
    $wt = git -C $RepoRoot worktree list 2>&1
    if ($LASTEXITCODE -eq 0) {
        $lines = ($wt -split "`n").Count
        Add-Check "git_worktrees" "WARN" "$lines worktrees on E: - only $RepoRoot is canonical"
    }
} catch {
    Add-Check "git_worktrees" "WARN" "git worktree list failed (ExFAT safe.directory?)"
}

# --- E: layout ---
$driveDirs = @(
    "E:\project-infi",
    "E:\lawful-shell-wt",
    "E:\nova-runtime-wt",
    "E:\urg-wt",
    "E:\mcps",
    "E:\.cursor"
)
foreach ($d in $driveDirs) {
    if (Test-Path $d) {
        Add-Check ("layout_" + ($d -replace '\\','_')) "PASS" "present"
    } else {
        Add-Check ("layout_" + ($d -replace '\\','_')) "WARN" "missing"
    }
}
if (Test-Path "E:\Voss Standalone") {
    $cnt = (Get-ChildItem "E:\Voss Standalone" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    if ($cnt -eq 0) {
        Add-Check "layout_voss_standalone" "WARN" "empty folder - remove or extract Voss Standalone.zip"
    }
}

# --- Summary ---
$results.summary = [ordered]@{
    pass = @($results.checks | Where-Object { $_.status -eq "PASS" }).Count
    warn = $warns
    fail = $fails
}

Write-Host ""
foreach ($c in $results.checks) {
    $color = switch ($c.status) { "PASS" { "Green" } "WARN" { "Yellow" } default { "Red" } }
    Write-Host ("[{0}] {1,-28} {2}" -f $c.status, $c.id, $c.detail) -ForegroundColor $color
}

Write-Host ""
if ($fails -gt 0) {
    Write-Host "AUDIT FAILED: $fails critical, $warns warnings" -ForegroundColor Red
} elseif ($warns -gt 0) {
    Write-Host "AUDIT OK WITH WARNINGS: $warns (review above)" -ForegroundColor Yellow
} else {
    Write-Host "AUDIT PASSED" -ForegroundColor Green
}

if ($JsonOut) {
    $results | ConvertTo-Json -Depth 6 | Set-Content -Path $JsonOut -Encoding UTF8
    Write-Host "Report: $JsonOut"
}

exit $(if ($fails -gt 0) { 1 } else { 0 })
