# Clean ephemeral OS/runtime artifacts only (per docs/audit/ROOT_STRUCTURE_AUDIT.md §3).
# Does NOT touch: src/, docs/, governance/, data/, tracked source.
param(
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root 'operator_kernel'))) {
    $Root = (Get-Location).Path
}

$Targets = @(
    (Join-Path $Root '.runtime'),
    (Join-Path $Root '.pytest_cache')
)

function Get-DirSizeMB([string]$Path) {
    if (-not (Test-Path $Path)) { return 0 }
    $bytes = (Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    if ($null -eq $bytes) { return 0 }
    return [math]::Round($bytes / 1MB, 2)
}

Write-Host "Root: $Root"
foreach ($t in $Targets) {
    $mb = Get-DirSizeMB $t
    $exists = Test-Path -LiteralPath $t
    Write-Host ("  {0,-20} exists={1} size~{2} MB" -f $t, $exists, $mb)
}

if ($WhatIf) {
    Write-Host "`nWhatIf: would remove only .runtime and .pytest_cache under $Root"
    exit 0
}

foreach ($t in $Targets) {
    if (Test-Path -LiteralPath $t) {
        Write-Host "Removing $t ..."
        Remove-Item -LiteralPath $t -Recurse -Force -ErrorAction Stop
        Write-Host "  done."
    }
}

Write-Host "`nCleanup complete. Freed ephemeral runtime/ops artifacts only."
