#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$ServiceName = "AAESDropboxWatcherService",
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
$ProjectPath = Join-Path $Root "services\windows-dropbox-service\AAES.DropboxWatcherService.csproj"
$RuntimeRoot = Join-Path $Root ".runtime\dropbox-service"
$PublishDir = Join-Path $RuntimeRoot "publish"
$ConfigPath = Join-Path $RuntimeRoot "dropbox-service.json"
$EnvPath = Join-Path $RuntimeRoot "dropbox-service.env"
$LogPath = Join-Path $RuntimeRoot "dropbox-service.log"
$ServiceExe = Join-Path $PublishDir "AAES.DropboxWatcherService.exe"
$TsxExecutable = Join-Path $Root "node_modules\.bin\tsx.CMD"
$WatchScript = Join-Path $Root "scripts\watch-dropbox-sync.ts"
$DropboxFolderHelperPath = Join-Path $ScriptDir "find-dropbox-sync-folder.ps1"

function Test-RunningAsAdministrator {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-InstallerArgumentList {
    $scriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path }
    $arguments = @(
        '-NoProfile'
        '-ExecutionPolicy'
        'Bypass'
        '-File'
        $scriptPath
    )

    if ($PSBoundParameters.ContainsKey('ServiceName') -and $ServiceName) {
        $arguments += @('-ServiceName', [string]$ServiceName)
    }

    if ($PSBoundParameters.ContainsKey('Uninstall') -and $Uninstall) {
        $arguments += '-Uninstall'
    }

    if ($WhatIfPreference) {
        $arguments += '-WhatIf'
    }

    return $arguments | Where-Object { $_ -ne $null -and $_.ToString().Trim().Length -gt 0 }
}

if (-not $WhatIfPreference -and -not (Test-RunningAsAdministrator)) {
    if (-not $PSCommandPath) {
        throw "This installer must run elevated."
    }

    $installerArgs = Get-InstallerArgumentList
    Write-Host "Requesting administrator elevation to install the Windows service..."
    $process = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $installerArgs -Wait -PassThru
    exit $process.ExitCode
}

function Write-ServiceConfig {
    New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null

    $dropboxRoot = if ($env:REPO_DROPBOX_ROOT) { $env:REPO_DROPBOX_ROOT } else { "/team" }
    $accountScope = if ($env:REPO_DROPBOX_ACCOUNT_SCOPE) { $env:REPO_DROPBOX_ACCOUNT_SCOPE } elseif ($env:DROPBOX_ACCOUNT_SCOPE) { $env:DROPBOX_ACCOUNT_SCOPE } else { "auto" }
    if (Test-Path $DropboxFolderHelperPath) {
        . $DropboxFolderHelperPath
    }
    $syncFolderSelection = Get-DropboxSyncFolderSelection
    if ($syncFolderSelection -and $syncFolderSelection.AccountScope -and $accountScope -eq 'auto' -and $syncFolderSelection.AccountScope -ne 'explicit') {
        $accountScope = [string]$syncFolderSelection.AccountScope
    }
    $syncFolderRoot = [string]$syncFolderSelection.Path
    $selectedAccountScope = if ($syncFolderSelection -and $syncFolderSelection.AccountScope) { [string]$syncFolderSelection.AccountScope } else { $accountScope }
    $historyLimit = if ($env:REPO_DROPBOX_HISTORY_LIMIT) { [int]$env:REPO_DROPBOX_HISTORY_LIMIT } else { 5 }
    $watchDebounceMs = if ($env:REPO_DROPBOX_WATCH_DEBOUNCE_MS) { [int]$env:REPO_DROPBOX_WATCH_DEBOUNCE_MS } else { 2500 }
    $watchMinIntervalMs = if ($env:REPO_DROPBOX_WATCH_MIN_INTERVAL_MS) { [int]$env:REPO_DROPBOX_WATCH_MIN_INTERVAL_MS } else { 15000 }
    $watchPollIntervalMs = if ($env:REPO_DROPBOX_WATCH_POLL_INTERVAL_MS) { [int]$env:REPO_DROPBOX_WATCH_POLL_INTERVAL_MS } else { 5000 }
    $uploadBackend = if ($env:DROPBOX_TOKEN -and $syncFolderRoot) {
        "api+folder"
    } elseif ($env:DROPBOX_TOKEN) {
        "api"
    } elseif ($syncFolderRoot) {
        "folder"
    } else {
        "none"
    }

    $config = [ordered]@{
        ServiceName = $ServiceName
        RepoRoot = $Root
        CorepackExecutable = $TsxExecutable
        CorepackArguments = $WatchScript
        EnvFile = $EnvPath
        LogPath = $LogPath
        DropboxRoot = $dropboxRoot
        SyncFolderRoot = $syncFolderRoot
        AccountScope = $accountScope
        SelectedAccountScope = $selectedAccountScope
        UploadBackend = $uploadBackend
        HistoryLimit = $historyLimit
        RestartDelayMs = 5000
        WatchDebounceMs = $watchDebounceMs
        WatchMinIntervalMs = $watchMinIntervalMs
        WatchPollIntervalMs = $watchPollIntervalMs
    }

    $config | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $ConfigPath

    if ($syncFolderRoot) {
        Write-Host "Detected Dropbox sync folder root: $syncFolderRoot"
    }
    if ($accountScope) {
        Write-Host "Dropbox account scope preference: $accountScope"
    }
    if ($selectedAccountScope) {
        Write-Host "Dropbox account scope selection: $selectedAccountScope"
    }
    switch ($uploadBackend) {
        'api+folder' { Write-Host "Dropbox upload mode: API preferred, Dropbox desktop folder fallback enabled" }
        'api' { Write-Host "Dropbox upload mode: API preferred" }
        'folder' { Write-Host "Dropbox upload mode: Dropbox desktop folder fallback" }
        default { Write-Host "Dropbox upload mode: disabled" }
    }

    if ($env:DROPBOX_TOKEN) {
        @(
            "DROPBOX_TOKEN=$($env:DROPBOX_TOKEN)"
            "REPO_DROPBOX_ROOT=$dropboxRoot"
            if ($accountScope) { "REPO_DROPBOX_ACCOUNT_SCOPE=$accountScope" }
            if ($selectedAccountScope) { "REPO_DROPBOX_SELECTED_ACCOUNT_SCOPE=$selectedAccountScope" }
            if ($syncFolderRoot) { "REPO_DROPBOX_SYNC_FOLDER_ROOT=$syncFolderRoot" }
            "REPO_DROPBOX_HISTORY_LIMIT=$historyLimit"
            "REPO_DROPBOX_WATCH_DEBOUNCE_MS=$watchDebounceMs"
            "REPO_DROPBOX_WATCH_MIN_INTERVAL_MS=$watchMinIntervalMs"
            "REPO_DROPBOX_WATCH_POLL_INTERVAL_MS=$watchPollIntervalMs"
        ) | Where-Object { $_ -ne $null } | Set-Content -Encoding UTF8 $EnvPath
    }
    elseif ($syncFolderRoot) {
        @(
            "REPO_DROPBOX_ROOT=$dropboxRoot"
            if ($accountScope) { "REPO_DROPBOX_ACCOUNT_SCOPE=$accountScope" }
            if ($selectedAccountScope) { "REPO_DROPBOX_SELECTED_ACCOUNT_SCOPE=$selectedAccountScope" }
            "REPO_DROPBOX_SYNC_FOLDER_ROOT=$syncFolderRoot"
            "REPO_DROPBOX_HISTORY_LIMIT=$historyLimit"
            "REPO_DROPBOX_WATCH_DEBOUNCE_MS=$watchDebounceMs"
            "REPO_DROPBOX_WATCH_MIN_INTERVAL_MS=$watchMinIntervalMs"
            "REPO_DROPBOX_WATCH_POLL_INTERVAL_MS=$watchPollIntervalMs"
        ) | Set-Content -Encoding UTF8 $EnvPath
    }
}

function Install-Service {
    if (-not (Test-Path $ProjectPath)) {
        throw "Missing Windows service project at $ProjectPath"
    }

    if (-not $PSCmdlet.ShouldProcess($ServiceName, "Publish and register Windows service")) {
        return
    }

    New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
    dotnet publish $ProjectPath -c Release -r win-x64 --self-contained false -o $PublishDir
    Write-ServiceConfig

    if (-not (Test-Path $ServiceExe)) {
        throw "Published service executable not found at $ServiceExe"
    }

    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existing) {
        Stop-Service -Name $ServiceName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        & sc.exe delete $ServiceName | Out-Null
        Start-Sleep -Seconds 2
    }

    $binaryPath = "`"$ServiceExe`" --config `"$ConfigPath`""
    New-Service -Name $ServiceName -BinaryPathName $binaryPath -DisplayName "AAES-OS Dropbox Watcher" -StartupType Automatic | Out-Null
    & sc.exe description $ServiceName "AAES-OS Dropbox watcher that auto-starts as a Windows service and syncs major repo changes." | Out-Null
    & sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/5000/restart/5000 | Out-Null
    & sc.exe failureflag $ServiceName 1 | Out-Null
    Start-Service -Name $ServiceName

    Write-Host "Installed Windows service '$ServiceName'."
    Write-Host "Config: $ConfigPath"
    Write-Host "Logs: $LogPath"
}

function Uninstall-Service {
    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $existing) {
        Write-Host "Service '$ServiceName' is not installed."
        return
    }

    if (-not $PSCmdlet.ShouldProcess($ServiceName, "Remove Windows service")) {
        return
    }

    Stop-Service -Name $ServiceName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    & sc.exe delete $ServiceName | Out-Null

    Write-Host "Removed Windows service '$ServiceName'."
}

if ($Uninstall) {
    Uninstall-Service
} else {
    Install-Service
}
