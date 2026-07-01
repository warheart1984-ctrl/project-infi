# Lawful Nova Agentic Shell - PowerShell profile
# Linked to $PROFILE by bootstrap.ps1

$NovaRepoRoot = $env:LAWFUL_NOVA_REPO_ROOT
if (-not $NovaRepoRoot) {
    $NovaRepoRoot = Split-Path $PSScriptRoot -Parent
}

$NovarcPath = Join-Path $env:USERPROFILE ".novarc.ps1"
if (Test-Path $NovarcPath) { . $NovarcPath }

if ($env:NOVA_VOSS_RUNTIME_PATH -and (Test-Path $env:NOVA_VOSS_RUNTIME_PATH)) {
    $env:Path = "$env:NOVA_VOSS_RUNTIME_PATH;$env:Path"
}
if ($env:NOVA_RSL_PATH -and (Test-Path $env:NOVA_RSL_PATH)) {
    $env:Path = "$env:NOVA_RSL_PATH;$env:Path"
}

$NvmHome = Join-Path $env:USERPROFILE ".nvm"
if (Test-Path (Join-Path $NvmHome "nvm.exe")) {
    $env:NVM_HOME = $NvmHome
    $env:NVM_SYMLINK = Join-Path $env:USERPROFILE "nodejs"
    $env:Path = "$env:NVM_SYMLINK;$env:NVM_HOME;$env:Path"
}

$Global:NovaReceiptLog = "$HOME\nova-receipts.jsonl"
$Global:NovaPolicyVersion = "CRK-1.0.0"
$SubstrateRegistryPath = "$HOME\nova-substrates.json"
$SubstrateCapsPath = "$HOME\nova-substrate-capabilities.json"
if (Test-Path $SubstrateRegistryPath) {
    $Global:NovaSubstrates = Get-Content -Raw $SubstrateRegistryPath | ConvertFrom-Json
} else {
    $Global:NovaSubstrates = $null
}
if (Test-Path $SubstrateCapsPath) {
    $Global:NovaSubstrateCapabilities = Get-Content -Raw $SubstrateCapsPath | ConvertFrom-Json
} else {
    $Global:NovaSubstrateCapabilities = $null
}

$NovaModels = @{
    "codex" = "qwen2.5-coder:3b"
    "deepseek" = "deepseek-coder:6.7b"
    "qwen" = "qwen2.5-coder:3b"
    "qwen7" = "qwen2.5-coder:7b"
    "coding-substrate" = "coding-substrate-1:latest"
    "analysis" = "gemma4:latest"
}

function global:Get-NovaSha256 {
    param([Parameter(Mandatory = $true)][string]$Text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    return ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join ""
}

function global:Invoke-NovaModel {
    param(
        [Parameter(Mandatory = $true)][string]$ModelKey,
        [Parameter(Mandatory = $true)][string]$Prompt
    )

    $modelName = $NovaModels[$ModelKey]
    if (-not $modelName) {
        Write-Host "Unknown model key: $ModelKey" -ForegroundColor Yellow
        return
    }
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        throw "ollama is required for Nova substrate routing, but it was not found on PATH."
    }

    ollama run $modelName $Prompt
}

function global:Invoke-NovaCodexPrompt {
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

function global:Write-NovaReceipt {
    param(
        [Parameter(Mandatory = $true)][string]$Prompt,
        [Parameter(Mandatory = $true)][string]$Result,
        [string]$ModelKey = "codex"
    )

    $receiptBlock = ""
    if ($Result -match "(?s)## Receipt\s*(.+)$") {
        $receiptBlock = $Matches[1].Trim()
    }

    $parentId = $Global:LastEventId
    $timestamp = (Get-Date).ToString("o")
    $baseEntry = [ordered]@{
        nodeId = "nova-node-1"
        substrateId = $NovaModels[$ModelKey]
        policyVersion = $Global:NovaPolicyVersion
        timestamp = $timestamp
        prompt = $Prompt
        receipt = $receiptBlock
        parentId = $parentId
    }
    $baseJson = $baseEntry | ConvertTo-Json -Depth 8 -Compress
    $hash = Get-NovaSha256 -Text $baseJson
    $eventId = $hash
    $entry = [ordered]@{
        nodeId = "nova-node-1"
        substrateId = $NovaModels[$ModelKey]
        policyVersion = $Global:NovaPolicyVersion
        eventId = $eventId
        parentId = $parentId
        timestamp = $timestamp
        prompt = $Prompt
        receipt = $receiptBlock
        hash = $hash
    }
    $receiptJson = $entry | ConvertTo-Json -Depth 8 -Compress
    [System.IO.File]::AppendAllText($Global:NovaReceiptLog, $receiptJson + [Environment]::NewLine)
    $Global:LastEventId = $eventId
    return $entry
}

function global:Invoke-NovaCodex {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    $fullPrompt = Invoke-NovaCodexPrompt -UserPrompt $Prompt -AsPrompt
    $result = Invoke-NovaModel -ModelKey "codex" -Prompt $fullPrompt
    $null = Write-NovaReceipt -Prompt $Prompt -Result ($result | Out-String) -ModelKey "codex"
    return $result
}

function global:Invoke-NovaReplay {
    param([Parameter(Mandatory = $true)][string]$EventId)
    if (-not (Test-Path $Global:NovaReceiptLog)) {
        Write-Host "No receipt log found: $Global:NovaReceiptLog" -ForegroundColor Yellow
        return
    }

    $entry = Get-Content $Global:NovaReceiptLog |
        Where-Object { $_.Trim() } |
        ForEach-Object { $_ | ConvertFrom-Json } |
        Where-Object { $_.eventId -eq $EventId } |
        Select-Object -First 1

    if (-not $entry) {
        Write-Host "No receipt found for eventId: $EventId" -ForegroundColor Yellow
        return
    }

    $fullPrompt = Invoke-NovaCodexPrompt -UserPrompt $entry.prompt -AsPrompt
    $result = Invoke-NovaModel -ModelKey "codex" -Prompt $fullPrompt
    Write-Host "=== Original Receipt ==="
    Write-Host $entry.receipt
    Write-Host "`n=== Replayed Output ==="
    Write-Host $result
}

function global:nova-chat {
    $cmd = $env:NOVA_CLI
    if (-not $cmd) { $cmd = "nova" }
    & $cmd chat
}

function global:nova-codex {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    Invoke-NovaCodex -Prompt $Prompt
}

function global:nova-deepseek {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    Invoke-NovaModel -ModelKey "deepseek" -Prompt $Prompt
}

function global:nova-qwen {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    Invoke-NovaModel -ModelKey "qwen" -Prompt $Prompt
}

function global:nova-analysis {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    Invoke-NovaModel -ModelKey "analysis" -Prompt $Prompt
}

function global:novr {
    Write-Host "[Nova] Reviewing staged changes..." -ForegroundColor Cyan
    git status
    git diff --cached
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Review these staged git changes. Identify any issues. Then write a conventional commit message and commit."
}

function global:novtest {
    Write-Host "[Nova] Running test suite..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Run all tests in this project. If any fail, identify the root cause and fix the source code. Re-run until all pass. Max 5 iterations."
}

function global:novpr {
    Write-Host "[Nova] Creating PR..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Compare this branch to main. Generate a conventional PR title and a detailed description (What, Why, How to test). Then run: gh pr create --title '<title>' --body '<body>'"
}

function global:novdoc {
    Write-Host "[Nova] Generating documentation..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Analyze all source files in the current directory. Generate comprehensive documentation and write it to README.md."
}

function global:novsec {
    Write-Host "[Nova] Running security audit..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Perform a thorough security audit of this codebase. Check for: hardcoded secrets, injection vulnerabilities, insecure dependencies, missing auth checks. Output a severity-ranked report."
}

function global:novrefactor {
    param([Parameter(Mandatory = $true)][string]$File)
    Write-Host "[Nova] Refactoring $File..." -ForegroundColor Cyan
    $cmd = $env:NOVA_CLI; if (-not $cmd) { $cmd = "nova" }
    & $cmd run "Refactor $File for improved readability, maintainability, and performance. Preserve all existing behavior and public API. Run tests after."
}

function global:novstack {
    Write-Host "[Nova] Stack Status" -ForegroundColor Cyan
    Write-Host "  API:     $($env:NOVA_API_URL)"
    $codingSubstrate = if ($env:NOVA_CODING_SUBSTRATE) { $env:NOVA_CODING_SUBSTRATE } else { "coding-substrate-1" }
    Write-Host "  Coding substrate: $codingSubstrate (qwen2.5-coder:3b, tier 15)"
    $gpu = "N/A"
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        $gpu = (nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1)
    }
    Write-Host "  GPU:     $gpu"
    Write-Host "  Cortex:  $($env:NOVA_CORTEX_PATH)"
    Write-Host "  Voss:    $($env:NOVA_VOSS_RUNTIME_PATH)"
    Write-Host "  GoW cfg: $($env:NOVA_GOW_CONFIG)"
    $url = if ($env:NOVA_API_URL) { $env:NOVA_API_URL } else { "http://localhost:8080" }
    try {
        $null = Invoke-WebRequest -Uri "$url/health" -UseBasicParsing -TimeoutSec 3
        Write-Host "  Health:  OK - API responding" -ForegroundColor Green
    } catch {
        Write-Host "  Health:  FAIL - API not responding" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[Nova] Lawful Nova shell ready (PowerShell)." -ForegroundColor Green
Write-Host "   nova-chat  | nova-codex  | nova-deepseek  | nova-qwen  | nova-analysis"
Write-Host "   novr       | novtest     | novdoc         | novstack"
$codingSubstrate = if ($env:NOVA_CODING_SUBSTRATE) { $env:NOVA_CODING_SUBSTRATE } else { "coding-substrate-1" }
Write-Host "   Coding substrate: $codingSubstrate (qwen2.5-coder:3b, tier 15)"
Write-Host ""
