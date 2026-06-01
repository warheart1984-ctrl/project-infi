param(
    [string]$NewKey,
    [string]$EnvPath = ".env",
    [switch]$VerifyOnly
)

Set-StrictMode -Version Latest
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

function Mask-Key {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return "<missing>"
    }
    if ($Value.Length -le 8) {
        return ("*" * $Value.Length)
    }
    return "{0}...{1}" -f $Value.Substring(0, 4), $Value.Substring($Value.Length - 4)
}

function Read-EnvValue {
    param([string]$Path, [string]$Name)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    $line = Get-Content -LiteralPath $Path | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -Last 1
    if (-not $line) {
        return $null
    }
    return ($line -split "=", 2)[1].Trim()
}

$resolvedEnvPath = if ([System.IO.Path]::IsPathRooted($EnvPath)) {
    $EnvPath
} else {
    Join-Path -Path $repoRoot -ChildPath $EnvPath
}
$envValue = Read-EnvValue -Path $resolvedEnvPath -Name "OPENROUTER_API_KEY"
$processValue = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "Process")
$userValue = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$machineValue = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "Machine")

Write-Host "OpenRouter key audit"
Write-Host "  .env path: $resolvedEnvPath"
Write-Host "  .env value: $(Mask-Key $envValue)"
Write-Host "  process env: $(Mask-Key $processValue)"
Write-Host "  user env: $(Mask-Key $userValue)"
Write-Host "  machine env: $(Mask-Key $machineValue)"

if ($VerifyOnly -or [string]::IsNullOrWhiteSpace($NewKey)) {
    Write-Host ""
    Write-Host "No local replacement applied."
    Write-Host "Next steps:"
    Write-Host "  1. Create a new key in the OpenRouter dashboard."
    Write-Host "  2. Re-run this script with -NewKey."
    Write-Host "  3. Restart AAIS, verify one OpenRouter turn, then revoke the old dashboard key."
    exit 0
}

if (-not (Test-Path -LiteralPath $resolvedEnvPath)) {
    New-Item -ItemType File -Path $resolvedEnvPath -Force | Out-Null
}

$lines = @()
if (Test-Path -LiteralPath $resolvedEnvPath) {
    $lines = Get-Content -LiteralPath $resolvedEnvPath
}

$updated = $false
$nextLines = foreach ($line in $lines) {
    if ($line -match "^\s*OPENROUTER_API_KEY\s*=") {
        $updated = $true
        "OPENROUTER_API_KEY=$NewKey"
    }
    else {
        $line
    }
}

if (-not $updated) {
    $nextLines += "OPENROUTER_API_KEY=$NewKey"
}

Set-Content -LiteralPath $resolvedEnvPath -Value $nextLines -Encoding UTF8

Write-Host ""
Write-Host "Updated .env with the new OpenRouter key: $(Mask-Key $NewKey)"
Write-Host "Remaining manual step: revoke the old key in the OpenRouter dashboard after backend verification."
