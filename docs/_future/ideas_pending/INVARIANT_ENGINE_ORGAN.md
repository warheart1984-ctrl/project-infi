# Invariant Engine Organ

CISIV stage: **concept**

Status: pending — Alt-9 summon wave `alt9-summon-wave-2026-06`.

## 1. Purpose

Formalize **Invariant Engine** ([`src/invariant_engine.py`](../../src/invariant_engine.py))
as a governed Alt-9 organ: read-only Nova-runtime consumer attestation for anchor
and bounded realtime invariant comparison without autonomous BLOCK escalation.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Subordinate to Nova operating contract;
engine compares only; Jarvis retains authority.

## 3. Non-Goals

- No autonomous immune BLOCK from engine alone
- No Super Nova activation
- No replacement for full bridge invariant paths in UGR/cognitive bridge

## 4. Organ Contract

Schema: [schemas/invariant_engine_organ.v1.json](./schemas/invariant_engine_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `aais.invariant_engine` |
| `nova_runtime_consumer` | Nova companion path invokes read-only comparison |
| `bridge_validation_posture` | Last bounded bridge/realtime validation summary |
| `layer_invariant_count` | Super Nova structural layer invariants observed |

## 5. Runtime (Proposed)

- `GET /api/jarvis/invariant-engine/status` — read-only invariant engine snapshot
- `src/invariant_engine_organ.py` — wraps engine + Nova comparison hook

## 6. Failsafe

Missing bridge or pipeline context returns idle snapshot; organ remains read-only.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns engine snapshot | `none_yet` | Requires MVP |
| Nova runtime consumer attested | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/INVARIANT_ENGINE_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/invariant_engine_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + `make invariant-engine-organ-gate` |

## 9. Related

- [NOVA_AI_OPERATING_CONTRACT.md](../../subsystems/nova/NOVA_AI_OPERATING_CONTRACT.md)
- [SUPER_NOVA_CANONICAL.md](../../_future/super_nova_expansion/SUPER_NOVA_CANONICAL.md)
- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt9-summon-wave-2026-06` — order **3** (after predictor organ)

**Depends on:** `realtime_event_cause_predictor_organ` concept; Nova anchor scaffold

**Minimal invariants:**

- Read-only compare — no autonomous escalation
- `nova_runtime_consumer` attestation on companion path
- Fail closed on missing bridge context
