# Scorpion Stage 0 Proof Bundle

## Claim

Stage 0 governance foundation: **proven** (file inventory present).

Stage 1+ runtime claims: see CI gate and `tests/test_scorpion.py` output.

## Evidence Inventory

| Artifact | Path |
|----------|------|
| Blueprint | `docs/subsystems/scorpion/SCORPION_BLUEPRINT.md` |
| CLI contract | `docs/subsystems/scorpion/SCORPION_CLI_CONTRACT.md` |
| Roadmap | `docs/subsystems/scorpion/SCORPION_ROADMAP.md` |
| Baseline checklist | `docs/subsystems/scorpion/BASELINE_CHECKLIST.md` |
| Invariant catalog | `scorpion/invariants/os_invariants.v1.json` |

## Verification Commands

```bash
py -3.12 -m unittest tests.test_scorpion -v
py -3.12 -m scorpion.scorpion --mode chaos-check --case-id sc-stage0
py -3.12 -m scorpion.scorpion --mode verify --case-id sc-stage0 --write-report docs/proof/scorpion/scorpion_verify_report.json
```

## Unresolved Assertions

- Kernel Sentinel: `asserted` (design only)
- Wolf CoG live ingest: `asserted` (inactive)
- Cross-machine replay: `asserted` (inactive)
