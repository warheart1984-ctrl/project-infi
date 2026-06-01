# Compact WSL Debian ext4.vhdx on C: after deleting files inside Linux.
# MUST run in an elevated (Administrator) PowerShell window.
#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$vhdx = Join-Path $env:LOCALAPPDATA "Packages\TheDebianProject.DebianGNULinux_76v4gfsz19hv4\LocalState\ext4.vhdx"
if (-not (Test-Path $vhdx)) {
    Write-Error "VHDX not found: $vhdx"
}

$before = (Get-Item $vhdx).Length
Write-Host "VHDX: $vhdx"
Write-Host "Size before: $([math]::Round($before / 1GB, 2)) GB"
Write-Host ""

Write-Host "1. Shutting down WSL..."
wsl --shutdown
Start-Sleep -Seconds 5

$lockers = @("wsl", "wslservice", "vmwp", "vmmem")
$running = Get-Process -Name $lockers -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "2. Processes still holding WSL (close Cursor WSL terminals, Docker, etc.):"
    $running | Format-Table Name, Id -AutoSize
    Write-Host "Waiting 15s..."
    Start-Sleep -Seconds 15
    $running = Get-Process -Name $lockers -ErrorAction SilentlyContinue
    if ($running) {
        Write-Host "Still locked. Stop WSL service, then retry compact:"
        Write-Host "  Stop-Service LxssManager -Force"
        exit 1
    }
}

Write-Host "3. Compacting with Optimize-VHD..."
try {
    Optimize-VHD -Path $vhdx -Mode Full
} catch {
    Write-Warning "Optimize-VHD failed: $($_.Exception.Message)"
    $diskpartScript = @"
select vdisk file="$vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit
"@
    $diskpartScript | diskpart
}

$after = (Get-Item $vhdx).Length
$freed = $before - $after
Write-Host ""
Write-Host "Size after:  $([math]::Round($after / 1GB, 2)) GB"
Write-Host "Reclaimed:   $([math]::Round($freed / 1GB, 2)) GB"
