# Tutorial 6 — Running CDP-1

## Purpose

CDP-1 measures continuity drift under controlled perturbations.

## Run baseline

```bash
python sdk/continuity-sdk/harness/cdp1_experiment.py
```

## With perturbations

See `docs/crk1/continuity/CDP1_CONSTITUTIONAL_SPEC.md` for protocol details.

## Metrics

- Drift score
- Continuity graphs
- Threshold comparison

## Reproduction

Full scripts live in `sdk/continuity-sdk/` and `replication/` (if present).

Publish results per [challenge protocol](../governance/CHALLENGES.md).
