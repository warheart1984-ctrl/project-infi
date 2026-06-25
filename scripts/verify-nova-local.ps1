# Read-only Nova + Cursor diagnostics (no restarts, no tunnel changes).
#
# Usage:
#   .\scripts\verify-nova-local.ps1
#   .\scripts\verify-nova-local.ps1 -BaseUrl http://127.0.0.1:8080
#   .\scripts\verify-nova-local.ps1 -Quick   # skip slow Nemotron chat probe

param(
    [string]$BaseUrl = "",
    [string]$ModelName = "lawful-nova",
    [switch]$Quick
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not $BaseUrl) {
    $port = if ($env:NOVA_PORT) { $env:NOVA_PORT } else { 8080 }
    $BaseUrl = "http://127.0.0.1:$port"
}

function Pass([string]$Msg) { Write-Host "  OK $Msg" -ForegroundColor Green }
function Warn([string]$Msg) { Write-Host "  WARN $Msg" -ForegroundColor DarkYellow }
function Fail([string]$Msg) { Write-Host "  FAIL $Msg" -ForegroundColor Red }

Write-Host "Nova local verify -> $BaseUrl" -ForegroundColor Cyan
$ok = $true

try {
    $health = Invoke-RestMethod -Uri "$($BaseUrl.TrimEnd('/'))/health" -TimeoutSec 5
    Pass "health status=$($health.status)"
    if ($health.frontier_configured) {
        Pass "frontier $($health.frontier_provider) / $($health.frontier_model)"
    } elseif ($health.frontier_provider) {
        Warn "frontier '$($health.frontier_provider)' not configured (check .env NVIDIA_API_KEY; restart Nova)"
        $ok = $false
    } else {
        Warn "no frontier provider (deterministic cortex only)"
    }
} catch {
    Fail "health unreachable: $_"
    exit 1
}

try {
    $models = Invoke-RestMethod -Uri "$($BaseUrl.TrimEnd('/'))/v1/models" -TimeoutSec 5
    $ids = @($models.data | ForEach-Object { $_.id })
    if ($ids -contains $ModelName) {
        Pass "/v1/models lists $ModelName"
    } else {
        Warn "/v1/models missing $ModelName (found: $($ids -join ', '))"
        $ok = $false
    }
} catch {
    Fail "/v1/models: $_"
    $ok = $false
}

if ($Quick -or -not $health.frontier_configured) {
    Write-Host ""
    if ($Quick) {
        Write-Host "Quick mode: skipped Nemotron chat probe." -ForegroundColor DarkGray
    } else {
        Write-Host "Skipped Nemotron chat probe (frontier not configured)." -ForegroundColor DarkGray
    }
} else {
    try {
        $body = @{
            model       = $ModelName
            messages    = @(@{ role = "user"; content = "reply ok" })
            max_tokens  = 16
            temperature = 0
        } | ConvertTo-Json -Depth 4 -Compress
        $resp = Invoke-RestMethod -Method Post `
            -Uri "$($BaseUrl.TrimEnd('/'))/v1/chat/completions" `
            -Headers @{ Authorization = "Bearer local-nova" } `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 180
        $snippet = ($resp.choices[0].message.content | Out-String).Trim()
        if ($snippet -match "Under RSL, Nova Cortex reads") {
            Warn "chat returned deterministic stub (X-Lawful-Nova-Frontier would be stub)"
            $ok = $false
        } else {
            Pass "Nemotron chat probe ($($snippet.Substring(0, [Math]::Min(60, $snippet.Length)))...)"
        }
    } catch {
        Warn "chat probe failed or timed out: $_"
        $ok = $false
    }
}

Write-Host ""
if ($ok) {
    Write-Host "Result: PASS" -ForegroundColor Green
    exit 0
}
Write-Host "Result: NEEDS ATTENTION" -ForegroundColor DarkYellow
Write-Host "Fix: .\scripts\start-nova-for-cursor.ps1 -FrontierProvider nvidia -SkipChatProbe"
Write-Host "Cursor: re-run without -NoTunnel for public URL"
exit 1
