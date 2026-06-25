# Start Lawful Nova for Cursor (local API + HTTPS tunnel via ngrok or Cloudflare).
#
# Cursor routes BYOK requests through its cloud backend, so localhost override
# fails unless Nova is reachable at a public HTTPS URL. This script starts Nova
# and opens a tunnel (ngrok or cloudflared) and prints exact Cursor settings.
#
# Usage:
#   .\scripts\start-nova-for-cursor.ps1
#   .\scripts\start-nova-for-cursor.ps1 -Port 8081
#   .\scripts\start-nova-for-cursor.ps1 -NoTunnel
#   .\scripts\start-nova-for-cursor.ps1 -Tunnel cloudflared
#   .\scripts\start-nova-for-cursor.ps1 -FrontierProvider openai
#   .\scripts\start-nova-for-cursor.ps1 -NgrokDomain scoreless-calzone-plant.ngrok-free.dev
#   .\scripts\start-nova-for-cursor.ps1 -TrafficPolicyFile scripts\ngrok\policy-cursor-dev.yaml

param(
    [int]$Port = 0,
    [string]$ModelName = "lawful-nova",
    [string]$ApiKeyPlaceholder = "local-nova",
    [switch]$NoTunnel,
    [ValidateSet("auto", "ngrok", "cloudflared")]
    [string]$Tunnel = "auto",
    [string]$NgrokExe = "",
    [string]$NgrokDomain = "",
    [string]$TrafficPolicyFile = "",
    [string]$CloudflaredExe = "",
    [string]$FrontierProvider = "",
    [int]$TunnelWaitSeconds = 30,
    [switch]$SkipChatProbe,
    [int]$ChatProbeTimeoutSec = 0
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if ($Port -le 0) {
    $Port = if ($env:NOVA_PORT) { [int]$env:NOVA_PORT } else { 8080 }
}

$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPy) {
    $PyExe = $VenvPy
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PyExe = (Get-Command python).Source
} else {
    throw "Python not found. Create venv: python -m venv .venv; .\.venv\Scripts\pip install -e `".[dev]`""
}

function Import-DotEnv([string]$Path, [string[]]$ForceKeys = @()) {
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $eq = $line.IndexOf("=")
        if ($eq -lt 1) { return }
        $key = $line.Substring(0, $eq).Trim()
        $value = $line.Substring($eq + 1).Trim().Trim('"').Trim("'")
        $force = $ForceKeys -contains $key
        if ($key -and $value -and ($force -or -not (Get-Item "env:$key" -ErrorAction SilentlyContinue))) {
            Set-Item -Path "env:$key" -Value $value
        }
    }
}

$NovaDotEnvForceKeys = @(
    "NVIDIA_API_KEY",
    "NOVA_FRONTIER_PROVIDER",
    "AAIS_NVIDIA_MODEL",
    "AAIS_NVIDIA_BASE_URL",
    "AAIS_NVIDIA_ENABLE_THINKING",
    "AAIS_NVIDIA_FORCE_NONEMPTY_CONTENT",
    "AAIS_NVIDIA_REASONING_BUDGET",
    "NOVA_NGROK_DOMAIN"
)

Import-DotEnv (Join-Path $Root ".env") -ForceKeys $NovaDotEnvForceKeys

$env:LAWFUL_NOVA_REPO_ROOT = $Root
$env:PYTHONPATH = $Root
$env:NOVA_PORT = "$Port"
$LocalBase = "http://127.0.0.1:$Port"
$env:NOVA_API_URL = $LocalBase

if ($FrontierProvider) {
    $env:NOVA_FRONTIER_PROVIDER = $FrontierProvider
    Write-Host "Frontier provider requested: $FrontierProvider (requires matching API key in .env)"
}

if (-not $NgrokDomain) {
    $NgrokDomain = $env:NOVA_NGROK_DOMAIN
}
if (-not $TrafficPolicyFile) {
    $defaultPolicy = Join-Path $Root "scripts\ngrok\policy-cursor-dev.yaml"
    if (Test-Path $defaultPolicy) {
        $TrafficPolicyFile = $defaultPolicy
    }
}

function Test-NovaHealth([string]$BaseUrl) {
    try {
        $health = Invoke-RestMethod -Uri "$($BaseUrl.TrimEnd('/'))/health" -TimeoutSec 3
        return [bool]($health.status -eq "ok")
    } catch {
        return $false
    }
}

function Test-NovaOpenAIModels([string]$BaseUrl, [string]$Model) {
    try {
        $models = Invoke-RestMethod -Uri "$($BaseUrl.TrimEnd('/'))/v1/models" -TimeoutSec 5
        $ids = @($models.data | ForEach-Object { $_.id })
        return ($ids -contains $Model) -or ($ids -contains "lawful-nova")
    } catch {
        return $false
    }
}

function Test-NovaOpenAI([string]$BaseUrl, [string]$Model, [int]$TimeoutSec = 60) {
    try {
        $body = @{
            model       = $Model
            messages    = @(@{ role = "user"; content = "ping" })
            max_tokens  = 16
            temperature = 0
        } | ConvertTo-Json -Depth 4 -Compress
        $resp = Invoke-RestMethod -Method Post `
            -Uri "$($BaseUrl.TrimEnd('/'))/v1/chat/completions" `
            -Headers @{ Authorization = "Bearer $ApiKeyPlaceholder" } `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec $TimeoutSec
        return ($resp.object -eq "chat.completion")
    } catch {
        return $false
    }
}

function Resolve-NgrokExe {
    param([string]$Explicit)
    if ($Explicit -and (Test-Path $Explicit)) { return $Explicit }
    $cmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $common = @(
        "$env:LOCALAPPDATA\Microsoft\WindowsApps\ngrok.exe",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ngrok.exe",
        "$env:ProgramFiles\ngrok\ngrok.exe",
        "$env:USERPROFILE\scoop\shims\ngrok.exe"
    )
    foreach ($path in $common) {
        if (Test-Path $path) { return $path }
    }
    return $null
}

function Resolve-CloudflaredExe {
    param([string]$Explicit)
    if ($Explicit -and (Test-Path $Explicit)) { return $Explicit }
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $common = @(
        "$env:ProgramFiles\Cloudflare\Cloudflare WARP\cloudflared.exe",
        "$env:ProgramFiles\cloudflared\cloudflared.exe",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\cloudflared.exe",
        "$env:USERPROFILE\scoop\shims\cloudflared.exe"
    )
    foreach ($path in $common) {
        if (Test-Path $path) { return $path }
    }
    return $null
}

function Test-NgrokConfigured([string]$Exe) {
    if ($env:NGROK_AUTHTOKEN -and $env:NGROK_AUTHTOKEN.Trim()) {
        return $true
    }
    if (-not $Exe) { return $false }
    try {
        $output = & $Exe config check 2>&1 | Out-String
        return ($LASTEXITCODE -eq 0) -and ($output -notmatch "authtoken|ERR_NGROK|cannot find the path")
    } catch {
        return $false
    }
}

function Test-TrafficPolicyBlocksCursor([string]$PolicyPath) {
    if (-not $PolicyPath -or -not (Test-Path $PolicyPath)) { return $false }
    $text = Get-Content $PolicyPath -Raw
    return ($text -match 'type:\s*oauth') -or ($text -match 'type:\s*deny')
}

function Start-NgrokTunnel {
    param(
        [string]$Exe,
        [int]$Port,
        [int]$WaitSeconds,
        [string]$Domain = "",
        [string]$PolicyFile = ""
    )
    if (-not (Test-NgrokConfigured $Exe)) {
        Write-Host ""
        Write-Host "ngrok is installed but not authenticated." -ForegroundColor DarkYellow
        Write-Host "ngrok path: $Exe"
        Write-Host ""
        Write-Host "Pick one (Windows):"
        Write-Host "  A) .\scripts\setup-ngrok-authtoken.ps1"
        Write-Host "  B) & `"$Exe`" config add-authtoken YOUR_TOKEN"
        Write-Host "  C) `$env:NGROK_AUTHTOKEN = 'YOUR_TOKEN'  (this session only)"
        Write-Host "  D) Edit config: & `"$Exe`" config edit  -> agent.authtoken: YOUR_TOKEN"
        Write-Host ""
        Write-Host "Then re-run:"
        if ($Domain) {
            Write-Host "  .\scripts\start-nova-for-cursor.ps1 -NgrokDomain $Domain"
        } else {
            Write-Host "  .\scripts\start-nova-for-cursor.ps1"
        }
        return $null
    }

    $ngrokEnv = @{}
    if ($env:NGROK_AUTHTOKEN) {
        $ngrokEnv["NGROK_AUTHTOKEN"] = $env:NGROK_AUTHTOKEN
    }

    $existing = Get-NgrokPublicUrl -WaitSeconds 1
    if ($existing) {
        Write-Host "Using existing ngrok tunnel: $existing"
        return $existing
    }

    if ($PolicyFile -and (Test-Path $PolicyFile)) {
        if (Test-TrafficPolicyBlocksCursor $PolicyFile) {
            Write-Host "WARN: Traffic policy may block Cursor (oauth/deny rules). Use scripts/ngrok/policy-cursor-dev.yaml" -ForegroundColor DarkYellow
        }
    }

    $ngrokArgs = @("http")
    if ($Domain) { $ngrokArgs += @("--url=$Domain") }
    if ($PolicyFile -and (Test-Path $PolicyFile)) {
        $ngrokArgs += @("--traffic-policy-file", (Resolve-Path $PolicyFile).Path)
    }
    $ngrokArgs += @("$Port")

    Write-Host "Starting ngrok: $Exe $($ngrokArgs -join ' ')"
    if ($ngrokEnv.Count -gt 0) {
        Start-Process -FilePath $Exe -ArgumentList $ngrokArgs -WindowStyle Minimized -Environment $ngrokEnv | Out-Null
    } else {
        Start-Process -FilePath $Exe -ArgumentList $ngrokArgs -WindowStyle Minimized | Out-Null
    }
    $publicBase = Get-NgrokPublicUrl -WaitSeconds $WaitSeconds
    if (-not $publicBase -and $Domain) {
        $publicBase = "https://$Domain"
        Write-Host "  Using reserved domain: $publicBase" -ForegroundColor Green
    }
    if (-not $publicBase) {
        Write-Host ""
        Write-Host "ngrok did not expose a public URL within ${WaitSeconds}s." -ForegroundColor DarkYellow
        Write-Host "Check http://127.0.0.1:4040 or run: ngrok http $Port"
        Write-Host "Common fix: ngrok config add-authtoken YOUR_TOKEN"
    }
    return $publicBase
}

function Get-NgrokPublicUrl {
    param([int]$WaitSeconds)
    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 2
            $https = @($tunnels.tunnels | Where-Object { $_.public_url -like "https://*" })
            if ($https.Count -gt 0) {
                return [string]$https[0].public_url
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    return $null
}

function Start-CloudflaredQuickTunnel {
    param(
        [string]$Exe,
        [int]$Port,
        [int]$WaitSeconds
    )
    $logFile = Join-Path $env:TEMP "nova-cloudflared-$Port.log"
    if (Test-Path $logFile) { Remove-Item $logFile -Force -ErrorAction SilentlyContinue }

    Start-Process -FilePath $Exe `
        -ArgumentList @(
            "tunnel",
            "--url", "http://127.0.0.1:$Port",
            "--logfile", $logFile,
            "--loglevel", "info"
        ) `
        -WindowStyle Hidden | Out-Null

    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    $pattern = 'https://[a-z0-9-]+\.trycloudflare\.com'
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $logFile) {
            $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
            if ($content -and ($content -match $pattern)) {
                return $Matches[0]
            }
        }
        Start-Sleep -Milliseconds 500
    }
    return $null
}

function Write-CursorInstructions {
    param(
        [string]$OpenAiBaseUrl,
        [string]$Model,
        [string]$ApiKey,
        [switch]$ViaTunnel,
        [string]$TunnelKind = ""
    )

    Write-Host ""
    Write-Host "========== Cursor Settings (Models) ==========" -ForegroundColor Cyan
    Write-Host "1. Cursor Settings -> Models"
    Write-Host "2. Enable: Override OpenAI Base URL"
    Write-Host "3. OpenAI Base URL:"
    Write-Host "   $OpenAiBaseUrl" -ForegroundColor Yellow
    Write-Host "4. OpenAI API Key (placeholder is fine):"
    Write-Host "   $ApiKey" -ForegroundColor Yellow
    Write-Host "5. Add custom model:"
    Write-Host "   $Model" -ForegroundColor Yellow
    Write-Host "6. Disable other models if needed; select $Model in Chat"
    Write-Host ""
    Write-Host "Requires Cursor Pro (or higher) for custom base URL."
    if ($ViaTunnel) {
        $kind = if ($TunnelKind) { $TunnelKind } else { "tunnel" }
        Write-Host "$kind exposes your local Nova to the internet - dev only." -ForegroundColor DarkYellow
    } else {
        Write-Host "127.0.0.1 will NOT work in Cursor Chat (cloud backend cannot reach localhost)." -ForegroundColor DarkYellow
    }
    Write-Host "==============================================" -ForegroundColor Cyan
}

function Write-TunnelInstallHelp {
    Write-Host ""
    Write-Host "No tunnel tool found. Install one of:" -ForegroundColor DarkYellow
    Write-Host "  ngrok:       https://ngrok.com/download"
    Write-Host "  cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    Write-Host ""
    Write-Host "Manual tunnel examples:"
    Write-Host "  ngrok http $Port"
    Write-Host "  cloudflared tunnel --url http://127.0.0.1:$Port"
    Write-Host ""
    Write-Host "Then set Cursor Base URL to: https://<tunnel-host>/v1"
}

Write-Host "Lawful Nova -> Cursor bootstrap" -ForegroundColor Green
Write-Host "Repo: $Root"
Write-Host "Local API: $LocalBase"

# --- Start Nova API ---
function Stop-NovaApiProcesses {
    param([int]$Port)
    try {
        $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        foreach ($listener in $listeners) {
            $proc = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
            if ($proc -and ($proc.ProcessName -match 'python')) {
                Write-Host "Stopping Nova API process (PID $($proc.Id)) ..."
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        # Best-effort stop for dev bootstrap.
    }
    Start-Sleep -Seconds 1
}

$novaWasRunning = Test-NovaHealth $LocalBase
$needsFrontierReload = $false
if ($novaWasRunning) {
    try {
        $runningHealth = Invoke-RestMethod -Uri "$LocalBase/health" -TimeoutSec 5
        if ($env:NOVA_FRONTIER_PROVIDER -and $env:NVIDIA_API_KEY -and -not $runningHealth.frontier_configured) {
            $needsFrontierReload = $true
            Write-Host "Nova is running without frontier configured; will restart to load .env ..."
        }
    } catch {
        # optional health read
    }
}
$mustRestart = $novaWasRunning -and ($FrontierProvider -or $env:NOVA_FRONTIER_PROVIDER -or $needsFrontierReload)
if ($mustRestart) {
    Write-Host "Restarting Nova API to apply frontier provider settings ..."
    Stop-NovaApiProcesses -Port $Port
    $novaWasRunning = $false
}

if ($novaWasRunning) {
    Write-Host "Nova API already running at $LocalBase/health"
} else {
    Write-Host "Starting Nova API on port $Port ..."
    Start-Process -FilePath $PyExe `
        -ArgumentList @("-m", "nova.api") `
        -WorkingDirectory $Root `
        -WindowStyle Hidden | Out-Null

    $started = $false
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 1
        if (Test-NovaHealth $LocalBase) { $started = $true; break }
    }
    if (-not $started) {
        throw "Nova API did not become healthy on $LocalBase. Check port $Port (try -Port 8081)."
    }
    Write-Host "  OK $LocalBase/health" -ForegroundColor Green
}

try {
    $health = Invoke-RestMethod -Uri "$LocalBase/health" -TimeoutSec 5
    if ($health.frontier_configured) {
        Write-Host "  OK frontier provider: $($health.frontier_provider) ($($health.frontier_model))" -ForegroundColor Green
    } elseif ($health.frontier_provider) {
        Write-Host "  WARN frontier provider '$($health.frontier_provider)' not configured (check .env keys)" -ForegroundColor DarkYellow
    } else {
        Write-Host "  INFO deterministic Nova cortex (no frontier provider). Use -FrontierProvider nvidia for Nemotron." -ForegroundColor DarkGray
    }
} catch {
    # health details optional
}

$frontierConfigured = $false
try {
    $frontierConfigured = [bool]$health.frontier_configured
} catch {
    $frontierConfigured = $false
}

if ($SkipChatProbe) {
    if (Test-NovaOpenAIModels $LocalBase $ModelName) {
        Write-Host "  OK /v1/models (chat probe skipped with -SkipChatProbe)" -ForegroundColor Green
    } else {
        Write-Host "WARN: /v1/models check failed." -ForegroundColor DarkYellow
    }
} elseif (-not $frontierConfigured) {
    if (Test-NovaOpenAIModels $LocalBase $ModelName) {
        Write-Host "  OK /v1/models (deterministic cortex; no Nemotron probe)" -ForegroundColor Green
    } else {
        Write-Host "WARN: /v1/models check failed." -ForegroundColor DarkYellow
    }
} else {
    $probeTimeout = if ($ChatProbeTimeoutSec -gt 0) { $ChatProbeTimeoutSec } else { 180 }
    if (Test-NovaOpenAI $LocalBase $ModelName -TimeoutSec $probeTimeout) {
        Write-Host "  OK OpenAI-compatible /v1/chat/completions (Nemotron, ${probeTimeout}s timeout)" -ForegroundColor Green
    } else {
        Write-Host "WARN: /v1/chat/completions Nemotron probe failed or timed out (${probeTimeout}s)." -ForegroundColor DarkYellow
        Write-Host "      API may still work; use scripts/verify-nova-local.ps1 or retry with -ChatProbeTimeoutSec 300"
        Write-Host "      Fast bootstrap: -SkipChatProbe"
    }
}

# --- Optional HTTPS tunnel ---
if (-not $NoTunnel) {
    $publicBase = $null
    $tunnelKind = ""

    $ngrok = if ($Tunnel -in @("auto", "ngrok")) { Resolve-NgrokExe -Explicit $NgrokExe } else { $null }
    $cloudflared = if ($Tunnel -in @("auto", "cloudflared")) { Resolve-CloudflaredExe -Explicit $CloudflaredExe } else { $null }

    if ($Tunnel -eq "ngrok" -and $ngrok) {
        $publicBase = Start-NgrokTunnel -Exe $ngrok -Port $Port -WaitSeconds $TunnelWaitSeconds -Domain $NgrokDomain -PolicyFile $TrafficPolicyFile
        if ($publicBase) {
            $tunnelKind = "ngrok"
            Write-Host "  OK ngrok -> $publicBase" -ForegroundColor Green
        }
    } elseif ($Tunnel -eq "cloudflared" -and $cloudflared) {
        Write-Host "Starting cloudflared quick tunnel on port $Port ..."
        $publicBase = Start-CloudflaredQuickTunnel -Exe $cloudflared -Port $Port -WaitSeconds $TunnelWaitSeconds
        if (-not $publicBase) {
            throw "cloudflared started but no trycloudflare.com URL within ${TunnelWaitSeconds}s."
        }
        $tunnelKind = "Cloudflare Tunnel"
        Write-Host "  OK cloudflared -> $publicBase" -ForegroundColor Green
    } elseif ($Tunnel -eq "auto") {
        if ($ngrok) {
            $publicBase = Start-NgrokTunnel -Exe $ngrok -Port $Port -WaitSeconds $TunnelWaitSeconds -Domain $NgrokDomain -PolicyFile $TrafficPolicyFile
            if ($publicBase) {
                $tunnelKind = "ngrok"
                Write-Host "  OK ngrok -> $publicBase" -ForegroundColor Green
            }
        }
        if (-not $publicBase -and $cloudflared) {
            Write-Host "ngrok unavailable; starting Cloudflare quick tunnel ..."
            $publicBase = Start-CloudflaredQuickTunnel -Exe $cloudflared -Port $Port -WaitSeconds $TunnelWaitSeconds
            if ($publicBase) {
                $tunnelKind = "Cloudflare Tunnel"
                Write-Host "  OK cloudflared -> $publicBase" -ForegroundColor Green
            }
        }
    }

    if ($publicBase) {
        $cursorBase = "$($publicBase.TrimEnd('/'))/v1"
        Write-CursorInstructions -OpenAiBaseUrl $cursorBase -Model $ModelName -ApiKey $ApiKeyPlaceholder -ViaTunnel -TunnelKind $tunnelKind
        Write-Host ""
        Write-Host "Quick tunnel test:"
        Write-Host "  curl `"$cursorBase/models`""
        Write-Host ""
        Write-Host "Leave Nova + $tunnelKind running in background processes."
        exit 0
    }

    if (-not $ngrok -and -not $cloudflared) {
        Write-TunnelInstallHelp
    } elseif ($NgrokDomain) {
        Write-Host ""
        Write-Host "Expected Cursor base URL after tunnel is up:" -ForegroundColor Cyan
        Write-Host "  https://$NgrokDomain/v1" -ForegroundColor Yellow
    }
    Write-CursorInstructions -OpenAiBaseUrl "https://YOUR-TUNNEL-HOST/v1" -Model $ModelName -ApiKey $ApiKeyPlaceholder
    exit 0
}

Write-CursorInstructions -OpenAiBaseUrl "$LocalBase/v1" -Model $ModelName -ApiKey $ApiKeyPlaceholder
Write-Host ""
Write-Host 'Local-only mode. For Cursor, re-run without -NoTunnel (auto: ngrok, then cloudflared).'
