# Mechanic Handoff Organ

CISIV stage: **concept**

Status: pending — Alt-10 summon wave `alt10-summon-wave-2026-06`.

## 1. Purpose

Observe Mechanic chat enforcement handoff state without mutating cases.

Wraps: [`mechanic/integration/chat_hook.py`](../../mechanic/integration/chat_hook.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous escalation or repo mutation
- No replacement of underlying governed subsystems

## 4. Organ Contract

Schema: [schemas/mechanic_handoff_organ.v1.json](./schemas/mechanic_handoff_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-MH-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/mechanic-handoff/status` — read-only status
- `src/mechanic_handoff_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/forensics/MECHANIC_HANDOFF_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/mechanic_handoff_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt10-summon-wave-2026-06` — order **5**

**Depends on:** `scorpion_bridge_organ`, `capability_service_bridge`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-MH-01`
