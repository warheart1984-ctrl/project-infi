# Perception Gateway Organ

CISIV stage: **concept**

Status: pending — Alt-14 summon wave `alt14-summon-wave-2026-06`.

## 1. Purpose

Read-only capability bridge perception catalog posture (vision env + bridge-safe flags).

Wraps: [`src/capability_service_bridge.py`](../../src/capability_service_bridge.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous route mutation or execution expansion
- No bypass of perception env gates
- No Super Nova or Dreamspace activation

## 4. Organ Contract

Schema: [schemas/perception_gateway_organ.v1.json](./schemas/perception_gateway_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-PGO-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/perception-gateway/status` — read-only status
- `src/perception_gateway_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/PERCEPTION_GATEWAY_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/perception_gateway_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt14-summon-wave-2026-06` — order **3**

**Depends on:** `ui_vision_organ`, `capability_module_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-PGO-01`
