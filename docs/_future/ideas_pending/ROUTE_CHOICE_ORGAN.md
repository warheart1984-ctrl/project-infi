# Route Choice Organ

CISIV stage: **concept**

Status: pending — Alt-14 summon wave `alt14-summon-wave-2026-06`.

## 1. Purpose

Read-only turn-level model route posture over MODEL_ROUTES; advisory only.

Wraps: [`src/model_routing.py`](../../src/model_routing.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous route mutation or execution expansion
- No bypass of perception env gates
- No Super Nova or Dreamspace activation

## 4. Organ Contract

Schema: [schemas/route_choice_organ.v1.json](./schemas/route_choice_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-RCO-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/route-choice/status` — read-only status
- `src/route_choice_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/ROUTE_CHOICE_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/route_choice_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt14-summon-wave-2026-06` — order **7**

**Depends on:** `perception_lane_organ`, `orchestration_spine_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-RCO-01`
