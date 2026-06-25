# One-time ngrok authtoken setup for Lawful Nova + Cursor.
#
# Usage:
#   cd E:\project-infi
#   .\scripts\setup-ngrok-authtoken.ps1
#   .\scripts\setup-ngrok-authtoken.ps1 -Authtoken "YOUR_TOKEN"
#
# Get token: https://dashboard.ngrok.com/get-started/your-authtoken
#
# Other options (same as ngrok docs):
#   ngrok config add-authtoken YOUR_TOKEN
#   ngrok config edit   ->  agent.authtoken: YOUR_TOKEN
#   $env:NGROK_AUTHTOKEN = "YOUR_TOKEN"   (current PowerShell session only)

param(
    [string]$Authtoken = "",
    [string]$NgrokExe = "",
    [switch]$EnvOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

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

$ngrok = Resolve-NgrokExe -Explicit $NgrokExe
if (-not $ngrok) {
    throw "ngrok not found. Install from Microsoft Store or https://ngrok.com/download"
}

Write-Host "Using ngrok: $ngrok" -ForegroundColor Green

if (-not $Authtoken) {
    if ($env:NGROK_AUTHTOKEN) {
        $Authtoken = $env:NGROK_AUTHTOKEN
        Write-Host "Using NGROK_AUTHTOKEN from environment."
    } else {
        Write-Host ""
        Write-Host "Open: https://dashboard.ngrok.com/get-started/your-authtoken"
        $Authtoken = Read-Host "Paste your ngrok authtoken"
    }
}

$Authtoken = $Authtoken.Trim()
if (-not $Authtoken) {
    throw "No authtoken provided."
}

if ($EnvOnly) {
    $env:NGROK_AUTHTOKEN = $Authtoken
    Write-Host "Set NGROK_AUTHTOKEN for this PowerShell session only." -ForegroundColor Green
} else {
    & $ngrok config add-authtoken $Authtoken
    if ($LASTEXITCODE -ne 0) {
        throw "ngrok config add-authtoken failed (exit $LASTEXITCODE)"
    }
    Write-Host "Saved authtoken to ngrok config (default: $env:LOCALAPPDATA\ngrok\ngrok.yml)." -ForegroundColor Green
}

Write-Host ""
Write-Host "Next:"
Write-Host "  cd $Root"
Write-Host "  .\scripts\start-nova-for-cursor.ps1 -NgrokDomain scoreless-calzone-plant.ngrok-free.dev"
