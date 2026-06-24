# IDC — Invariant Discovery Contract

Formal requirements for governed invariant discovery in response to drift and continuity failure.

## Core requirements

| ID | Requirement |
|----|-------------|
| IDC.1 | Initiated only on sustained CE(S)/SE(S) degradation or CF-event |
| IDC.2 | Evidence-first — references CF-events / drift traces |
| IDC.3 | Non-oracular — grounded in failure modes, stress tests, adversarial scenarios |
| IDC.4 | Governance integration — expressible, enforceable, testable |
| IDC.5 | Reproducible by non-founders from logs, metrics, receipts, harness output |

## Drift triggers

| Trigger | Condition | Action |
|---------|-----------|--------|
| **D1** | CE(S) < CE_min for duration T_ce, invariants satisfied | `DriftObservation` + open IDC channel |
| **D2** | SE(S) < SE_min for duration T_se | same |
| **D3** | CF-event with no invariant violation + full compliance | mark silent failure + open IDC channel |

Implementation: `InvariantDiscoveryContract.evaluate_ce_drift`, `evaluate_se_drift`, `evaluate_silent_cf_event`.

## Wire objects

| Type | Schema |
|------|--------|
| `DriftObservation` | `fixtures/crk1/drift_observation.schema.json` |
| `InvariantProposal` | `fixtures/crk1/invariant_proposal.schema.json` |
| `InvariantTestSuite` | `fixtures/crk1/invariant_test_suite.schema.json` |

## Pipeline

```
Drift / CF-event → DriftObservation → InvariantProposal → InvariantTestSuite → kernel amendment (governed)
```

Complements `KernelChallengeLoop` (revises/retires existing invariants).
