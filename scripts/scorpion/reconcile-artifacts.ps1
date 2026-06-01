$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root
$CaseId = if ($env:SCORPION_CASE_ID) { $env:SCORPION_CASE_ID } else { "sc-reconcile" }
$Trace = if ($env:SCORPION_TRACE) { $env:SCORPION_TRACE } else { "scorpion/fixtures/traces/fd_leak.ndjson" }
$FixedTs = if ($env:SCORPION_FIXED_TS) { $env:SCORPION_FIXED_TS } else { "2026-05-29T12:00:00Z" }
py -3.12 -m scorpion.scorpion --mode reconcile-artifacts `
  --case-id $CaseId `
  --trace-path $Trace `
  --fixed-timestamp $FixedTs `
  --proof-dir docs/proof/scorpion `
  --ledger-path .runtime/scorpion/anomaly_ledger.jsonl
