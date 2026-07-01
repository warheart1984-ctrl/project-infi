# NovaGovernance.psm1
# Importable governance helpers for Nova substrate routing, receipts, replay, and federation.

$Global:Nova = [ordered]@{
    nodeId = "nova-node-1"
    policyVersion = "CRK-1.0.0"
    receiptLog = "$HOME\nova-receipts.jsonl"
    federationLog = "$HOME\nova-federation.jsonl"
    driftResolutionLog = "$HOME\nova-drift-resolutions.jsonl"
    substrateRegistry = @{
        codex = "coding-substrate-1"
        deepseek = "deepseek-coder-v2"
        qwen = "qwen-governed-1"
        analysis = "analysis-1"
    }
    substrateCapabilities = @{
        "coding-substrate-1" = @{
            id = "coding-substrate-1"
            role = "codegen"
            capabilities = @("generate_code", "refactor_code", "explain_code", "write_tests")
            constraints = @("no_global_state", "no_unbounded_io", "no_external_network")
        }
        "qwen-governed-1" = @{
            id = "qwen-governed-1"
            role = "codegen"
            capabilities = @("generate_code", "refactor_code", "explain_code", "write_tests")
            constraints = @("no_global_state", "no_unbounded_io", "no_external_network")
        }
        "analysis-1" = @{
            id = "analysis-1"
            role = "analysis"
            capabilities = @("summarize_context", "explain_code", "write_docs")
            constraints = @("no_global_state", "no_unbounded_io", "no_external_network")
        }
    }
}

function Get-NovaSha256 {
    param([Parameter(Mandatory = $true)][string]$Text)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    return ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join ""
}

function Get-NovaSubstrateId {
    param([Parameter(Mandatory = $true)][string]$ModelKey)

    $substrateId = $Global:Nova.substrateRegistry[$ModelKey]
    if (-not $substrateId) {
        throw "Unknown Nova substrate key: $ModelKey"
    }
    return $substrateId
}

function New-NovaReceiptBase {
    param(
        [Parameter(Mandatory = $true)][string]$Prompt,
        [Parameter(Mandatory = $true)][string]$Receipt,
        [Parameter(Mandatory = $true)][string]$SubstrateId,
        [string]$ParentId = $Global:LastEventId,
        [string]$Timestamp = (Get-Date).ToString("o")
    )

    return [ordered]@{
        timestamp = $Timestamp
        nodeId = $Global:Nova.nodeId
        substrateId = $SubstrateId
        policyVersion = $Global:Nova.policyVersion
        prompt = $Prompt
        receipt = $Receipt
        parentId = $ParentId
    }
}

function Write-Receipt {
    param(
        [Parameter(Mandatory = $true)][string]$Prompt,
        [Parameter(Mandatory = $true)][string]$Result,
        [string]$ModelKey = "codex",
        [string]$LogPath = $Global:Nova.receiptLog
    )

    $receiptBlock = ""
    if ($Result -match "(?s)## Receipt\s*(.+)$") {
        $receiptBlock = $Matches[1].Trim()
    }

    $substrateId = Get-NovaSubstrateId -ModelKey $ModelKey
    $parentId = $Global:LastEventId
    $baseEntry = New-NovaReceiptBase -Prompt $Prompt -Receipt $receiptBlock -SubstrateId $substrateId -ParentId $parentId
    $baseJson = $baseEntry | ConvertTo-Json -Depth 8 -Compress
    $hash = Get-NovaSha256 -Text $baseJson
    $eventId = $hash

    $entry = [ordered]@{
        timestamp = $baseEntry.timestamp
        nodeId = $baseEntry.nodeId
        substrateId = $baseEntry.substrateId
        policyVersion = $baseEntry.policyVersion
        prompt = $baseEntry.prompt
        receipt = $baseEntry.receipt
        hash = $hash
        eventId = $eventId
        parentId = $baseEntry.parentId
    }

    $dir = Split-Path $LogPath -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force $dir | Out-Null
    }
    [System.IO.File]::AppendAllText($LogPath, (($entry | ConvertTo-Json -Depth 8 -Compress) + [Environment]::NewLine))
    $Global:LastEventId = $eventId
    return [pscustomobject]$entry
}

function Invoke-NovaModel {
    param(
        [Parameter(Mandatory = $true)][string]$ModelKey,
        [Parameter(Mandatory = $true)][string]$Prompt
    )

    $modelName = Get-NovaSubstrateId -ModelKey $ModelKey
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        throw "ollama is required for Nova substrate routing, but it was not found on PATH."
    }
    ollama run $modelName $Prompt
}

function Invoke-NovaCodexPrompt {
    param(
        [Parameter(Mandatory = $true)][string]$UserPrompt,
        [switch]$AsPrompt
    )

    $systemPrompt = @"
You are CODING-SUBSTRATE-1 inside the Nova lawful runtime.

Behave like OpenAI Codex, but with:
- structure (intent -> plan -> code -> receipt)
- no hallucinated APIs
- no hidden state
- deterministic outputs
- explicit reasoning

Produce output in the structure: Intent -> Plan -> Code -> Receipt.

User request:
$UserPrompt
"@

    if ($AsPrompt) { return $systemPrompt }
    return Invoke-NovaModel -ModelKey "codex" -Prompt $systemPrompt
}

function Invoke-NovaCodex {
    param([Parameter(Mandatory = $true)][string]$Prompt)

    $fullPrompt = Invoke-NovaCodexPrompt -UserPrompt $Prompt -AsPrompt
    $result = Invoke-NovaModel -ModelKey "codex" -Prompt $fullPrompt
    $null = Write-Receipt -Prompt $Prompt -Result ($result | Out-String) -ModelKey "codex"
    return $result
}

function Load-Ledger {
    param([string]$Path = $Global:Nova.receiptLog)

    if (-not (Test-Path $Path)) {
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

function Invoke-NovaReplay {
    param(
        [Parameter(Mandatory = $true)][string]$EventId,
        [string]$LogPath = $Global:Nova.receiptLog
    )

    $entry = Load-Ledger -Path $LogPath | Where-Object { $_.eventId -eq $EventId } | Select-Object -First 1
    if (-not $entry) {
        Write-Host "No receipt found for eventId: $EventId"
        return
    }

    $result = Invoke-NovaModel -ModelKey "codex" -Prompt $entry.prompt
    Write-Host "=== Original Receipt ==="
    Write-Host $entry.receipt
    Write-Host "`n=== Replayed Output ==="
    Write-Host $result
}

function Write-FederationReceipt {
    param(
        [Parameter(Mandatory = $true)][array]$NodesMerged,
        [Parameter(Mandatory = $true)][int]$MergedCount,
        [Parameter(Mandatory = $true)][int]$DriftCount,
        [string]$LogPath = $Global:Nova.federationLog
    )

    $event = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        eventType = "federation-merge"
        nodeId = $Global:Nova.nodeId
        policyVersion = $Global:Nova.policyVersion
        nodesMerged = $NodesMerged
        mergedCount = $MergedCount
        driftCount = $DriftCount
    }
    $hash = Get-NovaSha256 -Text ($event | ConvertTo-Json -Depth 8 -Compress)
    $event["hash"] = $hash
    $dir = Split-Path $LogPath -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force $dir | Out-Null
    }
    [System.IO.File]::AppendAllText($LogPath, (($event | ConvertTo-Json -Depth 8 -Compress) + [Environment]::NewLine))
    return [pscustomobject]$event
}

function Invoke-NovaFederate {
    param(
        [string]$Node1Log = "$HOME\nova-node1-receipts.jsonl",
        [string]$Node2Log = "$HOME\nova-node2-receipts.jsonl"
    )

    $node1 = Load-Ledger -Path $Node1Log
    $node2 = Load-Ledger -Path $Node2Log
    $merged = @($node1) + @($node2)
    $invalid = @($merged | Where-Object { -not (Test-ReceiptHash -Entry $_) })
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

function Resolve-Drift {
    param(
        [Parameter(Mandatory = $true)][string]$Prompt,
        [array]$Merged,
        [string]$LogPath = $Global:Nova.driftResolutionLog
    )

    if (-not $Merged) {
        $Merged = Load-Ledger
    }
    $entries = @($Merged | Where-Object { $_.prompt -eq $Prompt })
    if ($entries.Count -eq 0) {
        Write-Host "No drift entries found for prompt: $Prompt"
        return
    }

    Write-Host "Drift for prompt: $Prompt"
    for ($i = 0; $i -lt $entries.Count; $i++) {
        $entry = $entries[$i]
        Write-Host "[$i] node=$($entry.nodeId) substrate=$($entry.substrateId) hash=$($entry.hash)"
        Write-Host $entry.receipt
        Write-Host ""
    }

    $choice = Read-Host "Select canonical index"
    $canonical = $entries[[int]$choice]
    $resolution = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        eventType = "drift-resolution"
        nodeId = $Global:Nova.nodeId
        policyVersion = $Global:Nova.policyVersion
        prompt = $Prompt
        canonical = @{
            nodeId = $canonical.nodeId
            substrateId = $canonical.substrateId
            hash = $canonical.hash
        }
    }
    [System.IO.File]::AppendAllText($LogPath, (($resolution | ConvertTo-Json -Depth 8 -Compress) + [Environment]::NewLine))
    return [pscustomobject]$resolution
}

function Show-NovaContinuityGraph {
    param([string]$LogPath = $Global:Nova.receiptLog)

    $entries = Load-Ledger -Path $LogPath
    $groupedByHour = $entries | Group-Object {
        (Get-Date $_.timestamp).ToString("yyyy-MM-dd HH:00")
    }

    foreach ($group in $groupedByHour) {
        $count = $group.Count
        $bar = "#" * [Math]::Min($count, 50)
        Write-Host "$($group.Name) | $bar ($count)"
    }
}

function nova-codex {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    Invoke-NovaCodex -Prompt $Prompt
}

function nova-deepseek {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    Invoke-NovaModel -ModelKey "deepseek" -Prompt $Prompt
}

function nova-qwen {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    Invoke-NovaModel -ModelKey "qwen" -Prompt $Prompt
}

function nova-analysis {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    Invoke-NovaModel -ModelKey "analysis" -Prompt $Prompt
}

Export-ModuleMember -Function `
    Get-NovaSha256, `
    Invoke-NovaModel, `
    Invoke-NovaCodexPrompt, `
    Invoke-NovaCodex, `
    Invoke-NovaReplay, `
    Invoke-NovaFederate, `
    Resolve-Drift, `
    Show-NovaContinuityGraph, `
    Write-Receipt, `
    Write-FederationReceipt, `
    nova-codex, `
    nova-deepseek, `
    nova-qwen, `
    nova-analysis
