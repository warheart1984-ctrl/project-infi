# P3-3 Promotion Readiness Dry-Run Proof

Status: active evidence packet for `P3-3 Promotion readiness dry-run`.

## Scope

- Milestone: `P3-3`
- Purpose: prove Forge-tagged RC artifacts can pass stable promotion validation in dry-run mode without publishing.

## Claim Ledger

| Claim ID | Claim | Label | Why |
|---|---|---|---|
| C1 | Promotion source validator enforces Forge profile + scenario gates when profile is expected. | proven | `validate-promotion-source.py` requires profile attestation/validation, forge-build-state profile match, and scenarios `1,3,4,6` pass. |
| C2 | Local promotion dry-run fixture passes end-to-end validation chain. | proven | `promotion-dry-run.sh --skip-verify` against bundled fixture emits pass report. |
| C3 | Release workflow emits promotion dry-run report artifact in dry-run mode. | proven | `cogos-release.yml` now emits/uploads `promotion-dry-run-report.json` when `dry_run=true`. |
| C4 | RC workflow preserves Forge promotion artifacts in RC bundle. | proven | RC collect step tags `channel=forge-rc` and retains profile + forge-build-state artifacts when Forge profile active. |

## Verification Commands

```text
bash wolf-cog-os/scripts/test/promotion-dry-run.sh --skip-verify
python3 -m unittest tests.test_validate_promotion_source
python3 .github/scripts/validate-governance-ledger.py --mode fail
```

## Local Verification Outputs

```text
Promotion source validation: status=pass, source_run_id=424242, observed_run_id=424242, expected_profile=forge-selfhosted, observed_profile=forge-selfhosted, findings=0
promotion dry-run report: status=pass output=ci-artifacts/promotion-dry-run-report.json
promotion dry-run complete
Ran 6 tests in tests.test_validate_promotion_source OK
Governance ledger check: commands=23, warnings=0, errors=0, mode=fail
```

## Operator Dry-Run (GitHub)

Dispatch `CoGOS Stable Release` with:

- `dry_run=true`
- `source_run_id=<successful RC run id with forge-selfhosted>`
- `expected_profile_id=forge-selfhosted`
- `release_tag=<test tag>`

Expected artifacts:

- `promotion-source-validation.json` (status=pass)
- `promotion-dry-run-report.json` (status=pass)

## Blockers

- Live GitHub workflow-run evidence link still pending until first post-merge dispatch executes.
