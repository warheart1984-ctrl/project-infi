# Deliberation Organ

CISIV stage: **concept**

Status: pending — Alt-15 summon wave `alt15-summon-wave-2026-06`.

## 1. Purpose

Read-only cognitive.deliberation lobe posture (decision frames, criteria scores).

Wraps: [`src/cog_runtime/deliberation.py`](../../src/cog_runtime/deliberation.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of Jarvis executive or Nova cognitive turn configuration
- No lobe activation or routing override via organ API
- No Dreamspace or Super Nova autonomous escalation

## 4. Organ Contract

Schema: [schemas/deliberation_organ.v1.json](./schemas/deliberation_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-DLO-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/deliberation/status` — read-only status
- `src/deliberation_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/cognitive_runtime/DELIBERATION_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/deliberation_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [NOVA_COHERENCE_PROJECTION.md](../../runtime/NOVA_COHERENCE_PROJECTION.md)

## 10. Activation Order

**Batch:** `alt15-summon-wave-2026-06` — order **4**

**Depends on:** `coherence_projection_organ`, `route_choice_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-DLO-01`
