#Requires -Version 5.1
<#
.SYNOPSIS
  Operator red-team sweep: verify lawful paths work and unlawful paths stay blocked.

.EXAMPLE
  .\scripts\operator_red_team.ps1
  .\scripts\operator_red_team.ps1 -JsonOut .runtime\operator_red_team.json
#>
param(
    [string]$RepoRoot = "E:\project-infi",
    [string]$JsonOut = ""
)

$ErrorActionPreference = "Continue"
$RepoRoot = (Resolve-Path $RepoRoot).Path
if (Test-Path "$env:USERPROFILE\.novarc.ps1") { . "$env:USERPROFILE\.novarc.ps1" }

$checks = @()
$fails = 0

function Add-RT {
    param([string]$Id, [bool]$Ok, [string]$Detail)
    $status = if ($Ok) { "PASS" } else { "FAIL" }
    if (-not $Ok) { $script:fails++ }
    $script:checks += [ordered]@{ id = $Id; status = $status; detail = $Detail }
}

function Try-Http {
    param([string]$Method, [string]$Url, [string]$Body = $null)
    try {
        $params = @{ Uri = $Url; Method = $Method; TimeoutSec = 8; UseBasicParsing = $true }
        if ($Body) { $params.Body = $Body; $params.ContentType = "application/json" }
        $r = Invoke-WebRequest @params
        return @{ ok = $true; code = [int]$r.StatusCode; body = $r.Content }
    } catch {
        $code = 0
        $body = $_.Exception.Message
        if ($_.Exception.Response) {
            $code = [int]$_.Exception.Response.StatusCode
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $body = $reader.ReadToEnd()
            } catch { }
        }
        return @{ ok = $false; code = $code; body = $body }
    }
}

Write-Host "=== Operator Red Team ===" -ForegroundColor Cyan

# Lawful stack must respond
foreach ($pair in @(
    @{ id = "nova_health"; url = "http://127.0.0.1:8080/health" },
    @{ id = "aais_health"; url = "http://127.0.0.1:8000/health" },
    @{ id = "operator_health"; url = "http://127.0.0.1:8790/health" },
    @{ id = "brain_health"; url = "http://127.0.0.1:8791/health" }
)) {
    $t = Try-Http GET $pair.url
    Add-RT $pair.id ($t.ok -and $t.code -eq 200) "HTTP $($t.code) $($pair.url)"
}

# Lawful operator task create
$taskBody = '{"goal":"red team smoke - list workspace","title":"redteam"}'
$t = Try-Http POST "http://127.0.0.1:8790/agent/tasks" $taskBody
$taskOk = $t.ok -and $t.code -eq 200 -and ($t.body -match "task_id")
Add-RT "lawful_operator_task" $taskOk "POST /agent/tasks -> $($t.code)"

# Ungoverned AAIS agent path must stay blocked (503 within 3s)
$Py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $Py) {
    $probe = @"
import json, os, urllib.error, urllib.request
url = 'http://127.0.0.1:8000/agent/run'
body = json.dumps({'goal': 'redteam probe', 'session_id': 'redteam'}).encode()
req = urllib.request.Request(url, data=body, method='POST', headers={'Content-Type': 'application/json'})
try:
    urllib.request.urlopen(req, timeout=3)
    print('OPEN')
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}')
except Exception as e:
    print(type(e).__name__)
"@
    $agentProbe = & $Py -c $probe 2>&1 | Out-String
    $agentProbe = $agentProbe.Trim()
    $blocked = $agentProbe -match 'HTTP 503'
    if (-not $blocked -and $agentProbe -eq 'OPEN') {
        Add-RT "block_aais_agent_run" $false "agent/run returned 200 - restart AAIS with .novarc.ps1"
    } elseif (-not $blocked) {
        Add-RT "block_aais_agent_run" $false "agent/run probe: $agentProbe (restart AAIS if TimeoutError)"
    } else {
        Add-RT "block_aais_agent_run" $true "agent/run -> 503"
    }
}

# URG kill switch posture
$urgKill = $env:URG_MISSION_KILL_SWITCH -in @("1", "true", "yes", "on")
Add-RT "urg_kill_switch" $urgKill "URG_MISSION_KILL_SWITCH=$($env:URG_MISSION_KILL_SWITCH)"

$urgDry = ($env:URG_EXECUTION_MODE -eq "DRY_RUN") -or (-not $env:URG_EXECUTION_MODE)
Add-RT "urg_dry_run" $urgDry "URG_EXECUTION_MODE=$($env:URG_EXECUTION_MODE)"

# Unlawful plugs off
if (Test-Path $Py) {
    $dj = & $Py (Join-Path $RepoRoot "scripts\disable_unlawful_agents.py") --dry-run 2>&1 | Out-String
    try {
        $d = $dj | ConvertFrom-Json
        $stillOn = @($d.disabled_now | Where-Object { $_ })
        Add-RT "unlawful_plugs_off" ($stillOn.Count -eq 0) "enabled_unlawful=$($stillOn.Count)"
    } catch {
        Add-RT "unlawful_plugs_off" $false "could not parse disable_unlawful_agents output"
    }
}

# UL governed command gate (destructive verb blocked)
if (Test-Path $Py) {
    $ul = & $Py -c "from src.aais_ul_substrate import AAISULSubstrate; s=AAISULSubstrate(); a=s.execute_governed_command('cat jumps x2'); b=s.execute_governed_command('cat delete_repo x1'); print(int(a['allowed']), int(b['allowed']))" 2>&1
    $ulOk = ($ul -match "1 0")
    Add-RT "ul_forgegate" $ulOk "allowed=1 blocked=0 output=$ul"
}

Write-Host ""
foreach ($c in $checks) {
    $color = if ($c.status -eq "PASS") { "Green" } else { "Red" }
    Write-Host ("[{0}] {1,-24} {2}" -f $c.status, $c.id, $c.detail) -ForegroundColor $color
}

$summary = [ordered]@{
    red_team_version = "operator_red_team.v1"
    completed_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    pass = @($checks | Where-Object { $_.status -eq "PASS" }).Count
    fail = $fails
    checks = $checks
}

if ($JsonOut) {
    $summary | ConvertTo-Json -Depth 5 | Set-Content -Path $JsonOut -Encoding UTF8
    Write-Host "`nReport: $JsonOut"
}

if ($fails -gt 0) {
    Write-Host "`nRED TEAM FAILED: $fails check(s)" -ForegroundColor Red
    exit 1
}
Write-Host "`nRED TEAM PASSED" -ForegroundColor Green
exit 0
