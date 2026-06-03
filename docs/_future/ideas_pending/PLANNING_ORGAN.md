# Planning Organ

CISIV stage: **concept**

Status: pending — Alt-15 summon wave `alt15-summon-wave-2026-06`.

## 1. Purpose

Read-only cognitive.planning lobe posture (step chains, next_action).

Wraps: [`src/cog_runtime/planning.py`](../../src/cog_runtime/planning.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of Jarvis executive or Nova cognitive turn configuration
- No lobe activation or routing override via organ API
- No Dreamspace or Super Nova autonomous escalation

## 4. Organ Contract

Schema: [schemas/planning_organ.v1.json](./schemas/planning_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-PLO-02` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/planning/status` — read-only status
- `src/planning_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/cognitive_runtime/PLANNING_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/planning_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [NOVA_COHERENCE_PROJECTION.md](../../runtime/NOVA_COHERENCE_PROJECTION.md)

## 10. Activation Order

**Batch:** `alt15-summon-wave-2026-06` — order **5**

**Depends on:** `deliberation_organ`, `reflection_runtime_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-PLO-02`
