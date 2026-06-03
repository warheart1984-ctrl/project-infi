# OTEM Bounded Organ

CISIV stage: **concept**

Status: pending — Alt-12 summon wave `alt12-summon-wave-2026-06`.

## 1. Purpose

Read-only OTEM v5_frozen ceiling posture: proposal-only, no execution or workflow mutation.

Wraps: [`src/otem_runtime.py`](../../src/otem_runtime.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous escalation or repo mutation
- No replacement of underlying governed subsystems

## 4. Organ Contract

Schema: [schemas/otem_bounded_organ.v1.json](./schemas/otem_bounded_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-OTEM-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/otem-bounded/status` — read-only status
- `src/otem_bounded_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/OTEM_BOUNDED_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/otem_bounded_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt12-summon-wave-2026-06` — order **1**

**Depends on:** `cognitive_bridge_organ`, `safety_envelope_organ`, `operator_profile_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-OTEM-01`
