$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root
$CaseId = if ($env:SCORPION_CASE_ID) { $env:SCORPION_CASE_ID } else { "sc-weekly" }
$Trace = if ($env:SCORPION_TRACE) { $env:SCORPION_TRACE } else { "scorpion/fixtures/traces/fd_leak.ndjson" }
py -3.12 -m scorpion.scorpion --mode scan --case-id $CaseId --trace-path $Trace
py -3.12 -m scorpion.scorpion --mode verify --case-id $CaseId --write-verify-report docs/proof/scorpion/scorpion_verify_report.json
py -3.12 -m scorpion.scorpion --mode chaos-check --case-id $CaseId
py -3.12 -m scorpion.scorpion --mode drift-window-query --case-id $CaseId --window 5
