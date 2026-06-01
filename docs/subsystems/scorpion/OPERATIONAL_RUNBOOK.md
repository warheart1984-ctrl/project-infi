# Scorpion Operational Runbook (Skeleton)

## Setup

```bash
py -3.12 -m pip install -e .
py -3.12 -m unittest tests.test_scorpion -v
```

## Weekly Loop

Run `scripts/scorpion/weekly-loop.ps1` or `weekly-loop.sh`:

1. `scan` on canonical fixtures
2. `verify --write-report`
3. `chaos-check`
4. Append historian drift index if scan produced drift

## Monitoring (Outline)

- Watch `.runtime/scorpion/anomaly_ledger.jsonl` growth.
- Review `docs/proof/scorpion/health_drift_index.jsonl` trend via `drift-window-query`.

## Incident Response (Outline)

1. Run `trace-query` to detect hash drift.
2. Run `reconcile-query` for remediation ordering hints.
3. Do not use `apply` mode (blocked).

## CI Gate

`.github/workflows/scorpion-governance-gate.yml`
