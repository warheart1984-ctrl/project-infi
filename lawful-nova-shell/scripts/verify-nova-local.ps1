# Read-only Nova + Cursor diagnostics (delegates to project-infi).
#
# Usage:
#   .\lawful-nova-shell\scripts\verify-nova-local.ps1
#   .\lawful-nova-shell\scripts\verify-nova-local.ps1 -Quick

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$ShellRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ShellRoot
$ParentScript = Join-Path $RepoRoot "scripts\verify-nova-local.ps1"

if (-not (Test-Path $ParentScript)) {
    if ($env:LAWFUL_NOVA_REPO_ROOT) {
        $ParentScript = Join-Path $env:LAWFUL_NOVA_REPO_ROOT "scripts\verify-nova-local.ps1"
    }
}

if (-not (Test-Path $ParentScript)) {
    Write-Error "verify-nova-local.ps1 not found. Run from project-infi root or set LAWFUL_NOVA_REPO_ROOT."
    exit 1
}

& $ParentScript @RemainingArgs
