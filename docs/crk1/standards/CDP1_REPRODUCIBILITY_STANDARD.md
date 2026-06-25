# CDP-1 Reproducibility Standard

## Requirement 1 — Steward Independence

At least **3 stewards** must be:

- Independent
- Isolated
- Non-contaminated

## Requirement 2 — Deterministic Task

The judgment task must have:

- Stable scoring
- Known noise floor
- Defined contradiction class

## Requirement 3 — Lineage Consistency

All stewards must replay the **same** CRR-1 + CLG-1.

## Requirement 4 — Measurement Consistency

Governance must recompute all metrics from raw traces.

## Requirement 5 — Threshold Consistency

τA must be:

- Pre-declared
- Governance-approved
- Above noise floor

See [TA_SPEC.md](./TA_SPEC.md).

## Requirement 6 — Public Artifacts

All CDP-1 runs must publish:

| Artifact | Description |
|----------|-------------|
| `pre_trace.json` | Pre-assimilation judgment trace |
| `post_trace.json` | Post-assimilation judgment trace |
| `CAA1_receipt.json` | Continuity assimilation receipt |
| `validation_report.json` | Governance validation result |

## Related

- [CPRP.md](../research/CPRP.md)
- [CDP1_MULTI_STEWARD_PROTOCOL.md](../mission-006/CDP1_MULTI_STEWARD_PROTOCOL.md)
- [MISSION-006-REPRODUCTION-BUNDLE.md](../mission-006/MISSION-006-REPRODUCTION-BUNDLE.md)
