# Scorpion Stage 2 Proof Bundle

Claim: **proven** (historian index + query modes).

## Commands

```bash
py -3.12 -m scorpion.scorpion --mode scan --case-id sc-s2 --trace-path scorpion/fixtures/traces/memory_leak.ndjson
py -3.12 -m scorpion.scorpion --mode drift-window-query --case-id sc-s2 --window 5
py -3.12 -m scorpion.scorpion --mode snapshot-query --case-id sc-s2 --window 10
scripts/scorpion/weekly-loop.ps1
```

Artifact: `docs/proof/scorpion/health_drift_index.jsonl`
