# Weekly operator loop (BF-DOC-001). Non-destructive; dry-run only.
# Usage: powershell -File scripts/forgekeeper/weekly-operator-loop.ps1 [-FixedTimestamp "2026-05-28T12:00:00Z"]

param(
    [string]$PlanId = "bf-weekly",
    [string]$FixedTimestamp = "2026-05-28T12:00:00Z",
    [string]$VerifyReportPath = "docs/proof/bumblebee-forge/forgekeeper_verify_report.json"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

$base = @("py", "-3.12", "-m", "forge.forgekeeper", "--plan-id", $PlanId, "--scope", ".")

Write-Host "=== Step B: reconcile artifacts ==="
& @base --mode reconcile-artifacts --fixed-timestamp $FixedTimestamp `
  --proof-dir docs/proof/bumblebee-forge `
  --plan-artifact docs/proof/bumblebee-forge/stage2_attested_plan.json

Write-Host "=== Step C: verify export ==="
& @base --mode verify --fixed-timestamp $FixedTimestamp --write-report $VerifyReportPath

Write-Host "=== Step D: seam checks ==="
& @base --mode trace-query
& @base --mode reconcile-query
& @base --mode drift-window-query

Write-Host "=== Step E: chaos-check ==="
& @base --mode chaos-check

Write-Host "=== Step F: bundle-export ==="
& @base --mode bundle-export --fixed-timestamp $FixedTimestamp `
  --verify-report-path $VerifyReportPath `
  --write-bundle-export docs/proof/bumblebee-forge/forgekeeper_bundle_manifest.json

Write-Host "=== Done (review output; update STAGE1_PROOF_BUNDLE.md) ==="
