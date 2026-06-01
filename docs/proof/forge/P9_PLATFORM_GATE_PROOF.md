# P9 Platform Gate Proof Packet

Status: **Gate G approved** (Meta Architect 2026-05-28). Live CI URL debt tracked.

## Claim Ledger

| Claim ID | Claim | Label | Why |
|---|---|---|---|
| C1 | Platform gate consolidates P7-P9 checks | proven | `.github/scripts/check-forge-platform-gate.py` + green `ci-artifacts/forge-platform-gate-report.json` |
| C2 | Nightly evolution dry-run passes | proven | `bash wolf-cog-os/scripts/test/forge-nightly-evolution.sh --dry-run` |
| C3 | Lineage promotion wiring active | proven | `tests/test_validate_promotion_source.py` + fixture `forge-lineage.json` |
| C4 | Gate G platform-tier ship decision | **proven (approved)** | Meta Architect APPROVE recorded in `docs/forge-platform-gate.md` |

## Meta Architect Decision

| Field | Value |
|---|---|
| Decision | **APPROVE** — platform-tier Forge channel authorized |
| Decision date | 2026-05-28 |
| Scope | Platform contracts P7-P9 + dashboard |
| Rollback | Record HOLD or REJECT in `docs/forge-platform-gate.md`; revert platform CI gate wiring if required |

## Verification (one-click)

```bash
make forge-platform-gate
make forge-dashboard FORGE_DASHBOARD_ARGS="--check"
bash wolf-cog-os/scripts/test/promotion-dry-run.sh --skip-verify
```

## Verification outputs (local, 2026-05-28)

```text
make forge-platform-gate
  → forge platform gate: status=pass

make forge-dashboard FORGE_DASHBOARD_ARGS="--check"
  → platform-gate GREEN, forge-lineage GREEN

promotion-dry-run.sh --skip-verify
  → status=pass (forge-lineage.json in fixture)
```

## Artifacts

- `ci-artifacts/forge-platform-gate-report.json`
- `ci-artifacts/platform-gate-forge-lineage.json`
- `ci-artifacts/nightly-forge-lineage.json`

## Documentation debt

| Item | Owner | Due |
|---|---|---|
| Public CI workflow run URL | Operator | After merge to main |
| RC bundle with lineage artifacts | Operator | Next Forge RC run |
