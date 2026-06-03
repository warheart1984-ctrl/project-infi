# Realtime Event Cause Predictor Organ

CISIV stage: **concept**

Status: pending — Alt-9 summon wave `alt9-summon-wave-2026-06`.

## 1. Purpose

Formalize **Realtime Event-and-Cause Predictor**
([`src/realtime_event_cause_predictor.py`](../../src/realtime_event_cause_predictor.py))
as a governed Alt-9 organ: read-only attestation that the predictor is a live
runtime producer on the governed direct pipeline path.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Subordinate to governed direct pipeline;
predictions remain advisory through God Brain and Jarvis.

## 3. Non-Goals

- No new `rt` lane or tool calls on predictor path
- No duplicate inference logic in the organ wrapper
- No autonomous immune escalation from predictor output

## 4. Organ Contract

Schema: [schemas/realtime_event_cause_predictor_organ.v1.json](./schemas/realtime_event_cause_predictor_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `aais.realtime_event_cause_predictor` |
| `phase_registered` | Predictor component registered with phase gate |
| `live_runtime_producer` | Pipeline path includes valid predictor output |
| `last_rt_summary` | Bounded last interpreted state summary |

## 5. Runtime (Proposed)

- `GET /api/jarvis/realtime-predictor/status` — read-only predictor snapshot
- `src/realtime_event_cause_predictor_organ.py` — wraps predictor + pipeline attestation

## 6. Failsafe

Missing pipeline trace returns idle snapshot with `live_runtime_producer: false`.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns predictor snapshot | `none_yet` | Requires MVP |
| Live producer attested on pipeline | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/REALTIME_EVENT_CAUSE_PREDICTOR_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/realtime_event_cause_predictor_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + `make realtime-predictor-organ-gate` |

## 9. Related

- [REALTIME_EVENT_CAUSE_PREDICTION_MODULE.md](../../contracts/REALTIME_EVENT_CAUSE_PREDICTION_MODULE.md)
- [GOVERNED_DIRECT_PIPELINE.md](../../runtime/GOVERNED_DIRECT_PIPELINE.md)
- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt9-summon-wave-2026-06` — order **2** (after phase gate organ)

**Depends on:** `phase_gate_organ` concept; governed direct pipeline live path

**Minimal invariants:**

- Advisory-only predictions
- `live_runtime_producer` attestation, not duplicate inference
- No tool traffic on `rt` lane
