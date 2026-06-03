# Scorpion Bridge Organ

CISIV stage: **concept**

Status: pending — Alt-10 summon wave `alt10-summon-wave-2026-06`.

## 1. Purpose

Read-only Scorpion drift/ledger snapshot; documents Jarvis bridge gap.

Wraps: [`scorpion/scorpion.py`](../../scorpion/scorpion.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous escalation or repo mutation
- No replacement of underlying governed subsystems

## 4. Organ Contract

Schema: [schemas/scorpion_bridge_organ.v1.json](./schemas/scorpion_bridge_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-SB-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/scorpion-bridge/status` — read-only status
- `src/scorpion_bridge_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/forensics/SCORPION_BRIDGE_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/scorpion_bridge_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt10-summon-wave-2026-06` — order **4**

**Depends on:** `forensic_triangulation`, `governed_direct_pipeline`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-SB-01`
