# P4-1 First Shippable Forge Milestone Gate Proof

Status: active evidence packet for Gate F automation and ship readiness tracking.

## Scope

- Milestone: `P4-1`
- Canonical checklist: `docs/forge-shippable-gate.md`
- Gate report artifact: `ci-artifacts/forge-shippable-gate-report.json`

## Claim Ledger

| Claim ID | Claim | Label | Why |
|---|---|---|---|
| C1 | Automated local shippable gate consolidates B-E checks into one report. | proven | `check-forge-shippable-gate.py` runs governance, smoke, promotion dry-run, and regression tests. |
| C2 | Gate F RC artifact validation path exists. | proven | Checker accepts `--artifacts-dir` + `--source-run-id` and runs promotion source validation. |
| C3 | Forge is fully shippable today. | rejected | Meta Architect ship decision and live RC/promotion workflow-run URLs remain pending. |
| C4 | Public CI executes local shippable gate on every run. | proven | `cogos-ci-public.yml` invokes `make forge-shippable-gate`. |

## Verification Commands

```text
make forge-shippable-gate
python3 -m unittest tests.test_forge_shippable_gate
python3 .github/scripts/check-forge-shippable-gate.py --artifacts-dir wolf-cog-os/scripts/test/fixtures/promotion-forge-rc --source-run-id 424242 --expected-profile-id forge-selfhosted --mode fail
python3 .github/scripts/validate-governance-ledger.py --mode fail
```

## Meta Architect Gate F Decision

| Field | Value |
|---|---|
| Decision | **PENDING** |
| Required to approve | Green Forge RC run + release dry-run evidence URLs attached below |
| RC source run id | |
| RC workflow run url | |
| Release dry-run workflow run url | |
| P2-3 post-cutover workflow run url | |

## Local Verification Outputs

```text
forge shippable gate: status=pass output=ci-artifacts/forge-shippable-gate-report.json
Ran 8 tests in tests.test_forge_shippable_gate + tests.test_validate_promotion_source OK
Governance ledger check: commands=25, warnings=0, errors=0, mode=fail
```

## Remaining to close Gate F

1. Run Forge RC workflow with `forge_profile=forge-selfhosted`.
2. Dispatch stable release dry-run with that RC `source_run_id`.
3. Record Meta Architect **APPROVE** in this packet and `docs/forge-shippable-gate.md`.
