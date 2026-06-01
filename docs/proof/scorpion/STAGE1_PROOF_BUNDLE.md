# Scorpion Stage 1 Proof Bundle

Claim: **proven** (local unittest + scan on all invariant fixtures).

## Commands

```bash
py -3.12 -m unittest tests.test_scorpion.TestScorpionEvaluators -v
py -3.12 -m scorpion.scorpion --mode scan --case-id sc-s1 --trace-path scorpion/fixtures/traces/fd_leak.ndjson
py -3.12 -m scorpion.scorpion --mode chaos-check --case-id sc-s1
```

## Fixtures

All eight families under `scorpion/fixtures/traces/`.
