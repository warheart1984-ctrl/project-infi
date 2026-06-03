# AI Factory Organ

CISIV stage: **concept**

Status: pending — Alt-16 summon wave `alt16-summon-wave-2026-06`.

## 1. Purpose

Read-only AI Factory build/receipt posture; observes governed mind fabrication without deploy authority via organ surface.

Wraps: [`ai_factory/`](../../ai_factory/).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of Jarvis executive or contractor POST contract expansion
- No autonomous patch apply or Slingshot launch bypass via organ API
- No cross-machine replay claims at concept stage

## 4. Organ Contract

Schema: [schemas/ai_factory_organ.v1.json](./schemas/ai_factory_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-AFO-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/ai-factory/status` — read-only status
- `src/ai_factory_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/ai_factory/AI_FACTORY_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/ai_factory_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [AI_FACTORY.md](../../runtime/AI_FACTORY.md)
- [AI_SLINGSHOT.md](../../runtime/AI_SLINGSHOT.md)

## 10. Activation Order

**Batch:** `alt16-summon-wave-2026-06` — order **1**

**Depends on:** `capability_service_bridge`, `operator_cognition_coherence_fabric`, `nova_face_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-AFO-01`
