# Spatial Reasoning Organ

CISIV stage: **concept**

Status: pending — Alt-14 summon wave `alt14-summon-wave-2026-06`.

## 1. Purpose

Read-only spatial reasoning plug posture over bridge spatial capability.

Wraps: [`src/Spatial_reasoning.py`](../../src/Spatial_reasoning.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous route mutation or execution expansion
- No bypass of perception env gates
- No Super Nova or Dreamspace activation

## 4. Organ Contract

Schema: [schemas/spatial_reasoning_organ.v1.json](./schemas/spatial_reasoning_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-SRO-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/spatial-reasoning/status` — read-only status
- `src/spatial_reasoning_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/SPATIAL_REASONING_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/spatial_reasoning_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt14-summon-wave-2026-06` — order **4**

**Depends on:** `perception_gateway_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-SRO-01`
