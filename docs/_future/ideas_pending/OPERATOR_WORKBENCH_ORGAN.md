# Operator Workbench Organ

CISIV stage: **concept**

Status: pending — Alt-16 summon wave `alt16-summon-wave-2026-06`.

## 1. Purpose

Read-only evolving workbench workspace intel posture; proposal-only coding context.

Wraps: [`src/evolving_workbench.py`](../../src/evolving_workbench.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of Jarvis executive or contractor POST contract expansion
- No autonomous patch apply or Slingshot launch bypass via organ API
- No cross-machine replay claims at concept stage

## 4. Organ Contract

Schema: [schemas/operator_workbench_organ.v1.json](./schemas/operator_workbench_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-OWO-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/operator-workbench/status` — read-only status
- `src/operator_workbench_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/OPERATOR_WORKBENCH_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/operator_workbench_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [AI_FACTORY.md](../../runtime/AI_FACTORY.md)
- [AI_SLINGSHOT.md](../../runtime/AI_SLINGSHOT.md)

## 10. Activation Order

**Batch:** `alt16-summon-wave-2026-06` — order **8**

**Depends on:** `change_scope_organ`, `patchforge_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-OWO-01`
