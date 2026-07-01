param(
    [string]$Node1Log = "$HOME\nova-node1-receipts.jsonl",
    [string]$Node2Log = "$HOME\nova-node2-receipts.jsonl"
)

$NovaNodeId = "nova-node-1"
$NovaPolicyVersion = "CRK-1.0.0"
$FederationLog = "$HOME\nova-federation.jsonl"
$DriftResolutionLog = "$HOME\nova-drift-resolutions.jsonl"
$KnownSubstrates = @("coding-substrate-1", "qwen-governed-1", "analysis-1")

function Get-NovaSha256 {
    param([Parameter(Mandatory = $true)][string]$Text)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    return ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join ""
}

function Load-Ledger {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        Write-Host "Ledger not found: $Path"
        return @()
    }

    return Get-Content $Path |
        Where-Object { $_.Trim() } |
        ForEach-Object {
            try { $_ | ConvertFrom-Json } catch { $null }
        } |
        Where-Object { $_ -ne $null }
}

function Test-ReceiptHash {
    param([Parameter(Mandatory = $true)]$Entry)

    $baseEntry = [ordered]@{
        timestamp = $Entry.timestamp
        nodeId = $Entry.nodeId
        substrateId = $Entry.substrateId
        policyVersion = $Entry.policyVersion
        prompt = $Entry.prompt
        receipt = $Entry.receipt
        parentId = $Entry.parentId
    }
    $expected = Get-NovaSha256 -Text ($baseEntry | ConvertTo-Json -Depth 8 -Compress)
    return $expected -eq $Entry.hash
}

function Write-FederationReceipt {
    param(
        [Parameter(Mandatory = $true)][array]$NodesMerged,
        [Parameter(Mandatory = $true)][int]$MergedCount,
        [Parameter(Mandatory = $true)][int]$DriftCount
    )

    $federationEvent = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        eventType = "federation-merge"
        nodeId = $NovaNodeId
        policyVersion = $NovaPolicyVersion
        nodesMerged = $NodesMerged
        mergedCount = $MergedCount
        driftCount = $DriftCount
        substrates = $KnownSubstrates
    }
    $hash = Get-NovaSha256 -Text ($federationEvent | ConvertTo-Json -Depth 8 -Compress)
    $federationEvent["hash"] = $hash
    [System.IO.File]::AppendAllText($FederationLog, (($federationEvent | ConvertTo-Json -Depth 8 -Compress) + [Environment]::NewLine))
    return [pscustomobject]$federationEvent
}

function Resolve-Drift {
    param(
        [Parameter(Mandatory = $true)][string]$Prompt,
        [array]$Merged
    )

    $entries = @($Merged | Where-Object { $_.prompt -eq $Prompt })
    Write-Host "Drift for prompt: $Prompt"
    for ($i = 0; $i -lt $entries.Count; $i++) {
        $entry = $entries[$i]
        Write-Host "[$i] node=$($entry.nodeId) substrate=$($entry.substrateId) eventId=$($entry.eventId) hash=$($entry.hash)"
        Write-Host $entry.receipt
        Write-Host ""
    }

    $choice = Read-Host "Select canonical index"
    $canonical = $entries[[int]$choice]
    $resolution = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        eventType = "drift-resolution"
        nodeId = $NovaNodeId
        policyVersion = $NovaPolicyVersion
        prompt = $Prompt
        canonical = @{
            nodeId = $canonical.nodeId
            substrateId = $canonical.substrateId
            hash = $canonical.hash
        }
    }
    [System.IO.File]::AppendAllText($DriftResolutionLog, (($resolution | ConvertTo-Json -Depth 8 -Compress) + [Environment]::NewLine))
}

function Show-NovaContinuityGraph {
    param([string]$LogPath = "$HOME\nova-receipts.jsonl")

    $entries = Load-Ledger $LogPath
    $groupedByHour = $entries | Group-Object {
        (Get-Date $_.timestamp).ToString("yyyy-MM-dd HH:00")
    }

    foreach ($group in $groupedByHour) {
        $count = $group.Count
        $bar = "#" * [Math]::Min($count, 50)
        Write-Host "$($group.Name) | $bar ($count)"
    }
}

function Invoke-NovaFederate {
    param(
        [string]$LeftLog = $Node1Log,
        [string]$RightLog = $Node2Log
    )

    $node1 = Load-Ledger $LeftLog
    $node2 = Load-Ledger $RightLog
    $merged = @($node1) + @($node2)
    $invalid = @($merged | Where-Object { -not (Test-ReceiptHash $_) })
    $drift = @()

    foreach ($group in ($merged | Group-Object -Property prompt)) {
        $hashes = @($group.Group.hash | Select-Object -Unique)
        if ($hashes.Count -gt 1) {
            $drift += [pscustomobject]@{
                prompt = $group.Name
                nodes = @($group.Group.nodeId | Select-Object -Unique)
                substrates = @($group.Group.substrateId | Select-Object -Unique)
                hashes = $hashes
            }
        }
    }

    Write-Host "=== Federation Summary ==="
    Write-Host "Node1 entries: $($node1.Count)"
    Write-Host "Node2 entries: $($node2.Count)"
    Write-Host "Merged entries: $($merged.Count)"
    Write-Host "Invalid hashes: $($invalid.Count)"
    Write-Host ""
    Write-Host "=== Drift Events ==="
    if ($drift.Count -eq 0) {
        Write-Host "No drift detected."
    } else {
        foreach ($d in $drift) {
            Write-Host "Prompt: $($d.prompt)"
            Write-Host "Nodes:  $($d.nodes -join ', ')"
            Write-Host "Substrates: $($d.substrates -join ', ')"
            Write-Host "Hashes: $($d.hashes -join ', ')"
            Write-Host ""
        }
    }

    $nodesMerged = @($merged.nodeId | Select-Object -Unique)
    if ($nodesMerged.Count -eq 0) {
        $nodesMerged = @("nova-node-1", "nova-node-2")
    }
    $null = Write-FederationReceipt -NodesMerged $nodesMerged -MergedCount $merged.Count -DriftCount $drift.Count
    return [pscustomobject]@{
        merged = $merged
        drift = $drift
        invalid = $invalid
    }
}

Invoke-NovaFederate -LeftLog $Node1Log -RightLog $Node2Log | Out-Null
