# Co-builder loop — Help Wanted #4 + #8 proof (v1)

Status: **proven**

Labels: `help wanted`, `documentation`, `governance`, `python` — claims marked per [REPO_PROOF_LAW.md](../../REPO_PROOF_LAW.md)

## Issues addressed

| Issue | Deliverable | Label |
|-------|-------------|-------|
| #5 Governance dashboard guide | [GOVERNANCE_DASHBOARD_OPERATOR_GUIDE.md](../../operators/GOVERNANCE_DASHBOARD_OPERATOR_GUIDE.md) | **proven** |
| #8 Civilizational arc smoke | `make civilizational-arc-smoke` run below | **proven** |

## Reproduction — civilizational arc smoke

```bash
make civilizational-arc-smoke
```

Equivalent:

```bash
python -m pytest tests/test_inter_substrate_diplomacy_observe.py \
  tests/test_norm_federation_observe.py \
  tests/test_constitutional_evolution_observe.py \
  tests/test_federated_civilizational_epoch_observe.py -q
```

## Captured output (2026-06-08)

```
.............                                                            [100%]
13 passed in 15.27s
```

Exit code: **0**

## README / hub links

- [README.md](../../README.md) — governance dashboard guide linked from operator docs
- [HELP_WANTED_HUB.md](../../community/HELP_WANTED_HUB.md) — issues #5 and #8 marked delivered with proof links
- [CONTRIBUTING.md](../../CONTRIBUTING.md) — civilizational-arc-smoke listed for arc changes

## PR body template (co-builders)

```
## Summary
- Docs: governance dashboard operator guide (#4)
- Proof: civilizational-arc-smoke green

## Standing
- Dashboard guide structure: proven (contract-aligned)
- Smoke output: proven (13 passed)

## Test plan
- [x] make civilizational-arc-smoke
```
