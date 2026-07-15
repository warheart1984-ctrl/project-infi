#Requires -Version 5.1

function Resolve-DropboxSyncFolderRoot {
    param()

    $selection = Get-DropboxSyncFolderSelection
    return $selection.Path
}

function Get-DropboxSyncFolderSelection {
    param()

    $explicitCandidates = @(
        $env:REPO_DROPBOX_SYNC_FOLDER_ROOT
        $env:DROPBOX_SYNC_FOLDER_ROOT
        $env:DROPBOX_FOLDER_ROOT
        $env:DROPBOX_LOCAL_SYNC_FOLDER_ROOT
    ) | Where-Object { $_ -and $_.Trim().Length -gt 0 }

    foreach ($candidate in $explicitCandidates) {
        $resolvedCandidate = $candidate.Trim()
        if (Test-Path -LiteralPath $resolvedCandidate) {
            return [pscustomobject]@{
                Path = (Resolve-Path -LiteralPath $resolvedCandidate).Path
                AccountScope = 'explicit'
                Source = 'environment'
            }
        }
    }

    $preferredScope = Resolve-DropboxAccountScope
    $infoPaths = @(
        Join-Path $env:LOCALAPPDATA 'Dropbox\info.json'
        Join-Path $env:APPDATA 'Dropbox\info.json'
    ) | Where-Object { $_ -and (Test-Path $_) }

    foreach ($infoPath in $infoPaths) {
        try {
            $info = Get-Content -LiteralPath $infoPath -Raw | ConvertFrom-Json -ErrorAction Stop
        } catch {
            continue
        }

        $candidate = Get-DropboxPathFromInfoObject -Value $info -PreferredScope $preferredScope
        if ($candidate -and $candidate.Path -and (Test-Path -LiteralPath $candidate.Path)) {
            return [pscustomobject]@{
                Path = (Resolve-Path -LiteralPath $candidate.Path).Path
                AccountScope = $candidate.AccountScope
                Source = $infoPath
            }
        }
    }

    return [pscustomobject]@{
        Path = $null
        AccountScope = $preferredScope
        Source = 'unresolved'
    }
}

function Get-DropboxPathFromInfoObject {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Value,
        [string]$PreferredScope = 'auto'
    )

    $preferredKeys = Get-DropboxPreferredKeys -Scope $PreferredScope
    foreach ($key in $preferredKeys) {
        if ($Value.PSObject.Properties.Name -contains $key) {
            $candidate = Get-DropboxPathFromAccountObject -Value $Value.$key
            if ($candidate) {
                return [pscustomobject]@{
                    Path = $candidate
                    AccountScope = Convert-DropboxAccountKeyToScope -Key $key
                }
            }
        }
    }

    $fallback = Get-DropboxPathFromAccountObject -Value $Value
    if ($fallback) {
        return [pscustomobject]@{
            Path = $fallback
            AccountScope = $PreferredScope
        }
    }

    return $null
}

function Resolve-DropboxAccountScope {
    $scope = @(
        $env:REPO_DROPBOX_ACCOUNT_SCOPE
        $env:DROPBOX_ACCOUNT_SCOPE
    ) | Where-Object { $_ -and $_.Trim().Length -gt 0 } | Select-Object -First 1

    if (-not $scope) {
        return 'auto'
    }

    $normalized = $scope.Trim().ToLowerInvariant()
    switch ($normalized) {
        'business' { return 'business' }
        'team' { return 'business' }
        'work' { return 'business' }
        'personal' { return 'personal' }
        'auto' { return 'auto' }
        default { return 'auto' }
    }
}

function Get-DropboxPreferredKeys {
    param(
        [string]$Scope = 'auto'
    )

    switch ($Scope) {
        'business' { return @('business', 'team', 'work', 'personal') }
        'personal' { return @('personal', 'business', 'team', 'work') }
        default { return @('business', 'team', 'work', 'personal') }
    }
}

function Convert-DropboxAccountKeyToScope {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Key
    )

    switch ($Key.ToLowerInvariant()) {
        'business' { return 'business' }
        'team' { return 'business' }
        'work' { return 'business' }
        'personal' { return 'personal' }
        default { return 'auto' }
    }
}

function Get-DropboxPathFromAccountObject {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Value
    )

    if ($null -eq $Value) {
        return $null
    }

    $properties = $Value.PSObject.Properties.Name
    foreach ($name in @('path', 'root_path')) {
        if ($properties -contains $name) {
            $candidate = [string]$Value.$name
            if ($candidate.Trim().Length -gt 0) {
                return $candidate.Trim()
            }
        }
    }

    return $null
}
