# Events

Wire and calibration events in Continuity OS.

## CalibrationEvent

Canonical graph node produced when a correction is preserved.

| Field | Description |
|-------|-------------|
| `id` | CEV-* |
| `crr_id` | Linked CRR-1 |
| `steward_id` | Who was corrected |
| `channel_id` | Reality source |
| `calibration_delta` | Preserved shift |
| `related_grr_ids` | Optional GRR links |
| `invariant_implications` | e.g. `["K6"]` |

### Ingestion rule

Every validated CRR-1 **must** produce exactly one CalibrationEvent in CLG-1.

## CRK-1 wire events (v0.1)

| Type | Role |
|------|------|
| Identity | Steward / actor |
| Decision | Committed judgment |
| Outcome | Consequence |
| Evidence | Reality contact |
| Interpretation | Semantic frame |
| Receipt | Audit spine |

Envelope: `src/crk1/crk1_wire_v01.py`

## CFEvent — Continuity failure

Emitted by kernel challenge loop on invariant performance breach.

## Scheduler events

Internal mutations and drift tests recorded in mutation ledger — not public API events.

## Related

[Data Structures](data-structures.md) · [Lineage Queries](lineage-queries.md)
