# Slingshot Organ

CISIV stage: **concept**

Status: pending — Alt-16 summon wave `alt16-summon-wave-2026-06`.

## 1. Purpose

Read-only AI Slingshot kinetic accelerator posture (launch_blocked, MA-13 frame/packet).

Wraps: [`slingshot/`](../../slingshot/).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of Jarvis executive or contractor POST contract expansion
- No autonomous patch apply or Slingshot launch bypass via organ API
- No cross-machine replay claims at concept stage

## 4. Organ Contract

Schema: [schemas/slingshot_organ.v1.json](./schemas/slingshot_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-SLO-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/slingshot/status` — read-only status
- `src/slingshot_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/SLINGSHOT_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/slingshot_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [AI_FACTORY.md](../../runtime/AI_FACTORY.md)
- [AI_SLINGSHOT.md](../../runtime/AI_SLINGSHOT.md)

## 10. Activation Order

**Batch:** `alt16-summon-wave-2026-06` — order **7**

**Depends on:** `mechanic_handoff_organ`, `forensic_triangulation_organ`, `route_choice_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-SLO-01`
