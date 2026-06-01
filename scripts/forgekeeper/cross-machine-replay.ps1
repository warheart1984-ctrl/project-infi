# Forgekeeper cross-machine replay driver (inactive by default).
# Requires: FORGE_CROSS_MACHINE_REPLAY_ACTIVE=1 and filled REPLAY_MANIFEST.json

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$ManifestPath = Join-Path $RepoRoot "docs\proof\bumblebee-forge\cross_machine\REPLAY_MANIFEST.json"
$Active = $env:FORGE_CROSS_MACHINE_REPLAY_ACTIVE

if ($Active -ne "1") {
    Write-Output @{
        status = "inactive"
        claim_label = "asserted"
        message = "Cross-machine replay is built but not active. Set FORGE_CROSS_MACHINE_REPLAY_ACTIVE=1 to run."
        manifest_path = $ManifestPath
    } | ConvertTo-Json -Compress
    exit 0
}

if (-not (Test-Path $ManifestPath)) {
    Write-Error "REPLAY_MANIFEST.json missing. Copy REPLAY_MANIFEST.template.json and fill it first."
    exit 2
}

$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
if ($manifest.status -eq "inactive") {
    Write-Error "REPLAY_MANIFEST.json status is still inactive. Set status to active before replay."
    exit 2
}

Set-Location $RepoRoot
$transcript = @()
foreach ($cmd in $manifest.replay_commands) {
    $transcript += ">>> $cmd"
    Invoke-Expression $cmd 2>&1 | ForEach-Object { $transcript += "$_" }
    if ($LASTEXITCODE -ne 0) {
        $transcript += "EXIT=$LASTEXITCODE"
        break
    }
}

$OutDir = Join-Path $RepoRoot "docs\proof\bumblebee-forge\cross_machine"
$transcriptPath = Join-Path $OutDir "replay_transcript.txt"
$transcript -join "`n" | Set-Content $transcriptPath -Encoding utf8

Write-Output @{
    status = "active"
    claim_label = "asserted"
    message = "Replay completed; update manifest hashes and proof bundle before claiming proven."
    transcript_path = $transcriptPath
} | ConvertTo-Json -Compress
exit $LASTEXITCODE
