# Forge Risk Register

Status: lightweight active register  
Escalation: any triggered P0 risk routes to Meta Architect immediately

| ID | Risk | Owner role | Trigger | Mitigation | Contingency |
|---|---|---|---|---|---|
| R-01 | Profile/env precedence drift causes inconsistent builds | Seam Hunter | Same profile yields different resolved settings across runs | Define and test single precedence contract; emit resolved profile JSON in artifacts | Freeze Forge lane, revert to last known-good precedence map, re-run dry-run checks |
| R-02 | Governance ledger misses new Forge command consumers | Drift Watcher | `validate-governance-ledger.py` reports missing consumer or env mapping | Update `.github/governance/command-ledger.json` in same PR as command/workflow change | Block phase exit until ledger fail-mode passes |
| R-03 | Existing installer path regresses during Forge wiring | Bug Hunter | `make installer-smoke` or matrix required scenarios fail | Keep non-Forge behavior unchanged; run smoke/matrix checks per change | Stop-the-line on Forge changes, hotfix regression, rerun baseline |
| R-04 | Signing path bypassed in RC milestone | Operator | RC artifact bundle lacks `.minisig` or verify step fails | Enforce `SIGNING_REQUIRED=1` in RC Forge path; require verify output evidence | Reject milestone go decision and rerun RC with corrected signing config |
| R-05 | Wrong RC artifact promoted to stable dry-run | Inspector | Promotion input `source_run_id` does not match intended Forge run metadata | Verify run id, artifact naming prefix, and manifest before promotion gate | Cancel promotion attempt, regenerate release candidate evidence |
| R-06 | GRUB/profile seam breaks expected boot UX | Seam Hunter | `patch_grub_merge.sh` output diverges from approved Forge menu policy | Keep template-driven generation and add snapshot diff check on generated `grub.cfg` | Revert GRUB template change and restore prior known-good profile |
| R-07 | Warn-only drift debt accumulates and becomes invisible | Drift Watcher | Same warning repeats in 3 consecutive runs | Daily drift review with explicit owner + due date for each repeated warning | Escalate unresolved warning debt to Meta Architect for priority reset |

## Active Monitoring Commands

- `python3 .github/scripts/validate-governance-ledger.py --mode warn --summary-only`
- `python3 .github/scripts/validate-governance-ledger.py --mode fail`
- `make installer-smoke INSTALLER_ARGS="--state-dir /tmp/cogos-installer-state-local"`
- `INSTALLER_TEST_SCENARIOS="1,3,6" make installer-integration`
- `SIGNING_REQUIRED=1 make sign-artifacts ARTIFACT_DIR="ci-artifacts"`
- `make verify-artifacts ARTIFACT_DIR="ci-artifacts"`
