# Clean ephemeral OS-operation caches on drive C: only.
# Safe targets: user temp, pip/npm caches, Cursor editor caches, Windows temp (if writable).
# Does NOT touch: Program Files, Windows system, user Documents, project repos, governance, databases.
param(
    [switch]$WhatIf
)

$ErrorActionPreference = 'Continue'

function Get-DirSizeMB([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return 0 }
    try {
        $bytes = (Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum
        if ($null -eq $bytes) { return 0 }
        return [math]::Round($bytes / 1MB, 2)
    } catch {
        return 0
    }
}

function Clear-DirContents([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return 0 }
    $before = Get-DirSizeMB $Path
    if ($WhatIf) {
        Write-Host "  WhatIf: would clear $Path (~$before MB)"
        return $before
    }
    Get-ChildItem -LiteralPath $Path -Force -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction Stop
        } catch {
            Write-Warning "  skip: $($_.FullName) - $($_.Exception.Message)"
        }
    }
    $after = Get-DirSizeMB $Path
    $freed = [math]::Max(0, $before - $after)
    Write-Host "  cleared $Path (~$freed MB freed)"
    return $freed
}

$drive = Get-PSDrive -Name C -ErrorAction SilentlyContinue
if ($drive) {
    Write-Host ("C: free {0:N2} GB / used {1:N2} GB" -f ($drive.Free / 1GB), ($drive.Used / 1GB))
}

$Targets = @(
    $env:TEMP,
    (Join-Path $env:LOCALAPPDATA 'Temp'),
    (Join-Path $env:LOCALAPPDATA 'pip\cache'),
    (Join-Path $env:LOCALAPPDATA 'npm-cache'),
    (Join-Path $env:LOCALAPPDATA 'Cursor\Cache'),
    (Join-Path $env:LOCALAPPDATA 'Cursor\CachedData'),
    (Join-Path $env:LOCALAPPDATA 'Cursor\Code Cache'),
    (Join-Path $env:LOCALAPPDATA 'Cursor\GPUCache'),
    'C:\Windows\Temp'
)

Write-Host "`nScan (before):"
$totalBefore = 0
foreach ($t in $Targets) {
    if (Test-Path -LiteralPath $t) {
        $mb = Get-DirSizeMB $t
        $totalBefore += $mb
        Write-Host ("  {0,-55} ~{1,8} MB" -f $t, $mb)
    }
}
Write-Host ("  Total scannable cache ~{0:N1} MB" -f $totalBefore)

Write-Host "`nCleanup:"
$freed = 0
foreach ($t in $Targets) {
    $freed += Clear-DirContents $t
}

if (-not $WhatIf) {
    # Empty recycle bin on C: (current user)
    try {
        Clear-RecycleBin -Force -ErrorAction Stop
        Write-Host "  emptied Recycle Bin"
    } catch {
        Write-Warning "  Recycle Bin: $($_.Exception.Message)"
    }
}

$drive2 = Get-PSDrive -Name C -ErrorAction SilentlyContinue
if ($drive2) {
    Write-Host ("`nC: free now {0:N2} GB" -f ($drive2.Free / 1GB))
}
if ($WhatIf) {
    Write-Host "`nWhatIf complete - no files removed."
} else {
    Write-Host ("`nDone. Approx freed from listed caches: ~{0:N1} MB" -f $freed)
}
