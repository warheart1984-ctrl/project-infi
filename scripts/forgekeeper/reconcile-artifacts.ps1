# Refresh governance artifact linkage (report -> snapshot -> snapshot-index).
param(
    [string]$PlanId = "bf-reconcile",
    [string]$FixedTimestamp = "2026-05-28T12:00:00Z"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

py -3.12 -m forge.forgekeeper --mode reconcile-artifacts `
  --plan-id $PlanId --scope . --fixed-timestamp $FixedTimestamp `
  --proof-dir docs/proof/bumblebee-forge `
  --plan-artifact docs/proof/bumblebee-forge/stage2_attested_plan.json `
  --ledger-path .runtime/forgekeeper/decision_ledger.jsonl `
  --report-path docs/proof/bumblebee-forge/forgekeeper_report.json `
  --snapshot-path docs/proof/bumblebee-forge/forgekeeper_snapshot.json `
  --snapshot-index-path docs/proof/bumblebee-forge/forgekeeper_snapshot_index.jsonl
