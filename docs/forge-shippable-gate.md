# Forge Shippable Milestone Gate (Gate F)

Status: canonical Gate F checklist for first shippable Forge milestone (`forge-selfhosted`).

Authority: `META_ARCHITECT_LAWBOOK.md` > `docs/forge-build-program.md` > this document.

## Milestone definition

Forge is shippable when all required gates pass and Meta Architect records an explicit ship decision.

## Gate map

| Gate | Name | Owner | Required evidence |
|---|---|---|---|
| A | Program start / scope lock | Meta Architect | Backlog phases P0-P3 complete |
| B | Contract + governance integrity | Inspector | Governance ledger fail + repo safety pass |
| C | Forge ISO build path | Operator | `forge-iso-smoke.sh` pass |
| D | Promotion readiness | Operator | `promotion-dry-run.sh` pass + promotion validator tests |
| E | Installer/law regression | Bug Hunter | profile loader + law edge tests pass |
| F | RC artifact + ship decision | Meta Architect | Signed RC bundle + promotion validation + explicit approval |

## Automated local gate command

```bash
make forge-shippable-gate
```

Optional RC bundle validation:

```bash
python3 .github/scripts/check-forge-shippable-gate.py \
  --artifacts-dir ci-artifacts \
  --source-run-id <RC_RUN_ID> \
  --expected-profile-id forge-selfhosted \
  --mode fail
```

## Gate F go/no-go checklist

- [ ] Forge RC workflow produced signed + verified artifacts
- [ ] Required installer scenarios `1,3,4,6` passed in RC matrix summary
- [ ] Promotion source validation passes for RC `source_run_id`
- [ ] Stable release dry-run (`dry_run=true`) passes with `expected_profile_id=forge-selfhosted`
- [ ] Meta Architect records explicit **APPROVE** decision in proof packet

## Gate F automation (pipeline-driven)

When `COGOS_FORGE_PROFILE=forge-selfhosted`, self-hosted CI now:

- Validates substrate and emits `forge-lineage.json` with replay adapter provenance
- Emits pipeline cloud outputs (`raw-img`, `qcow2`) from `daily-driver.yaml`
- Runs nightly variant build on schedule (`make forge-nightly-build`)
- Runs Gate F preflight (`forge-gate-f-preflight.sh --strict`) before artifact upload

Host/local pipeline run:

```bash
make forge-run-pipeline PIPELINE=wolf-cog-os/forge/pipelines/daily-driver.yaml
```

## Meta Architect decision record

| Field | Value |
|---|---|
| Decision | pending |
| Decision date | |
| RC source run id | |
| Release dry-run workflow run url | |
| Notes | |

## Proof artifact

- Gate report: `ci-artifacts/forge-shippable-gate-report.json`
- Proof packet: `docs/proof/forge/P4-1_SHIPPABLE_GATE_PROOF.md`
