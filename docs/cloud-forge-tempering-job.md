# Cloud Forge Background Tempering Job (Phase 4)

Status: **active** (dry-run implementation; production CronJob is operator-deployed).

Authority: `docs/contracts/COLLECTIVE_PATTERN_LEDGER.md`, `src/cloud_forge/tempering.py`.

## Purpose

Mine `rail-decisions.jsonl` and cache layers overnight to:

- identify hot domains and EXPRESS-eligible patterns
- refresh L2 pattern hints for verified repeats
- emit a tempering report for operator review (no auto-promotion to Hall of Fame)

## Schedule (recommended)

| Environment | Cron | Mode |
|---|---|---|
| Dev | manual | `python -m src.cloud_forge.tempering --dry-run` |
| Staging | `0 2 * * *` | dry-run + report upload |
| Production | `0 3 * * *` | dry-run until Meta Architect approves live promotion |

## Command

```bash
py -3.12 -m src.cloud_forge.tempering --dry-run
```

Optional:

```bash
py -3.12 -m src.cloud_forge.tempering --dry-run --ledger-path docs/proof/cloud-forge/rail-decisions.jsonl --output ci-artifacts/cloud-forge-tempering-report.json
```

## Outputs

| Artifact | Path |
|---|---|
| JSON report | `ci-artifacts/cloud-forge-tempering-report.json` (default) |
| Summary | stdout |

Report fields: `domains_ranked`, `rail_counts`, `express_candidates`, `claim_status` (`asserted` for dry-run).

## Governance

- Tempering **never** bypasses COLLECTIVE_PATTERN_LEDGER verification gate.
- Live promotion requires explicit operator approval + proof bundle.
- Cross-tenant data must not appear in reports (aggregates only).

## Failsafe

On anomaly (S4+ rail failures spike), job SHOULD emit alert and skip L2 refresh — operator enables via `CLOUD_FORGE_TEMPERING_SKIP=1`.
