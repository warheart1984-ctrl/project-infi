# Connect Lawful Nova to Cursor (BYOK + public tunnel)
#
# Delegates to project-infi scripts when this shell lives inside the monorepo.
# Usage (from project-infi root):
#   .\lawful-nova-shell\scripts\start-nova-for-cursor.ps1
#   .\lawful-nova-shell\scripts\start-nova-for-cursor.ps1 -NgrokDomain your-subdomain.ngrok-free.dev

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$ShellRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ShellRoot
$ParentScript = Join-Path $RepoRoot "scripts\start-nova-for-cursor.ps1"

if (-not (Test-Path $ParentScript)) {
    if ($env:LAWFUL_NOVA_REPO_ROOT) {
        $ParentScript = Join-Path $env:LAWFUL_NOVA_REPO_ROOT "scripts\start-nova-for-cursor.ps1"
    }
}

if (-not (Test-Path $ParentScript)) {
    Write-Error @"
start-nova-for-cursor.ps1 was not found.

Cursor + NVIDIA frontier mode requires the full project-infi checkout (not standalone shell only).
Clone project-infi, install from repo root, then run:

  cd path\to\project-infi
  .\scripts\start-nova-for-cursor.ps1

See lawful-nova-shell/CURSOR.md for the full guide.
"@
    exit 1
}

& $ParentScript @RemainingArgs
