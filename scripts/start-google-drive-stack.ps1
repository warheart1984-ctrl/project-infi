[CmdletBinding()]
param(
    [int]$ApiPort = 4101,
    [int]$WebPort = 3001
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvPath = Join-Path $RepoRoot '.env'

if (-not (Test-Path -LiteralPath $EnvPath)) {
    throw "Missing $EnvPath"
}

foreach ($line in Get-Content -LiteralPath $EnvPath) {
    if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
    $name, $value = $line -split '=', 2
    if ($name.Trim()) { [Environment]::SetEnvironmentVariable($name.Trim(), $value, 'Process') }
}

$required = @('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_DRIVE_STATE_SECRET', 'GOOGLE_DRIVE_TOKEN_KEY')
$missing = @($required | Where-Object { [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($_, 'Process')) })
if ($missing.Count -gt 0) {
    throw "Missing required local setting(s): $($missing -join ', ')"
}

$env:PLATFORM_API_PORT = [string]$ApiPort
$env:PLATFORM_API_URL = "http://localhost:$ApiPort"
$env:PLATFORM_WEB_URL = "http://localhost:$WebPort"
$env:GOOGLE_DRIVE_REDIRECT_URI = "http://localhost:$WebPort/api/integrations/google-drive/callback"

$corepack = (Get-Command corepack.cmd -ErrorAction SilentlyContinue).Source
if (-not $corepack) {
    $bundled = Get-ChildItem -LiteralPath 'G:\.runtime' -Directory -Filter 'node-v*-win-x64' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
    if ($bundled) { $corepack = Join-Path $bundled.FullName 'corepack.cmd' }
}
if (-not $corepack -or -not (Test-Path -LiteralPath $corepack)) { throw 'corepack.cmd was not found' }

function Assert-PortFree([int]$Port) {
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $Port is already in use"
    }
}

Assert-PortFree $ApiPort
Assert-PortFree $WebPort

$runtimeLogs = Join-Path $RepoRoot '.local\google-drive\logs'
New-Item -ItemType Directory -Force -Path $runtimeLogs | Out-Null

$api = Start-Process -FilePath $corepack -ArgumentList @('pnpm', '--filter', '@aaes-os/platform-api', 'start') `
    -WorkingDirectory $RepoRoot -RedirectStandardOutput (Join-Path $runtimeLogs 'api.out.log') `
    -RedirectStandardError (Join-Path $runtimeLogs 'api.err.log') -WindowStyle Hidden -PassThru

$web = Start-Process -FilePath $corepack -ArgumentList @('pnpm', '--filter', '@aaes-os/platform-web', 'exec', 'next', 'dev', '-p', [string]$WebPort) `
    -WorkingDirectory $RepoRoot -RedirectStandardOutput (Join-Path $runtimeLogs 'web.out.log') `
    -RedirectStandardError (Join-Path $runtimeLogs 'web.err.log') -WindowStyle Hidden -PassThru

[pscustomobject]@{
    ApiPid = $api.Id
    WebPid = $web.Id
    ApiUrl = "http://localhost:$ApiPort"
    WebUrl = "http://localhost:$WebPort/integrations/google-drive"
    RedirectUri = $env:GOOGLE_DRIVE_REDIRECT_URI
    Logs = $runtimeLogs
}
