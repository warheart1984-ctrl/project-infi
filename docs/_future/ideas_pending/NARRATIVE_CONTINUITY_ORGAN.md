# Narrative Continuity Organ

CISIV stage: **concept**

Status: pending — Alt-8 summon wave `alt8-summon-wave-2026-06`.

## 1. Purpose

Formalize **Nova Narrative Continuity** metrics from
[`src/cog_runtime/narrative_continuity.py`](../../src/cog_runtime/narrative_continuity.py) as a
governed Alt-8 organ: read-only continuity score and persistence signals without
treating Narrative as authority or adding cognition lobes.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Subordinate to Jarvis routing;
Narrative remains observe-only per Nova v3 doctrine.

## 3. Non-Goals

- No new cognition lobes ([NARRATIVE_CONTINUITY_EVIDENCE_PLAN](../../proof/cognitive_runtime/NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md))
- No narrative routing or trust-pack synthesis in this organ
- No operator rubric study in v1 organ scope

## 4. Organ Contract

Schema: [schemas/narrative_continuity_organ.v1.json](./schemas/narrative_continuity_organ.v1.json)

| Field | Role |
|-------|------|
| `continuity_score` | Fraction of doing/done/toward filled |
| `story_persistence_rate` | Session-boundary story carry |
| `claim_label` | Evidence posture |

## 5. Runtime (Proposed)

- `GET /api/jarvis/narrative-continuity/status` — read-only continuity snapshot
- `src/narrative_continuity_organ.py` — wraps continuity scoring fixtures

## 6. Failsafe

Missing narrative store returns idle metrics with `claim_label: asserted`.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns continuity snapshot | `none_yet` | Requires MVP |
| A/B baseline beat proven in fixtures | `none_yet` | Requires gate |

Target proof packet: `docs/proof/cognitive_runtime/NARRATIVE_CONTINUITY_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/narrative_continuity_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + `make narrative-continuity-gate` |

## 9. Related

- [NOVA_CORTEX_V3_ROADMAP.md](../../runtime/NOVA_CORTEX_V3_ROADMAP.md)
- [NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md](../../proof/cognitive_runtime/NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md)
- [CONTINUITY_WITNESS_ORGAN.md](./CONTINUITY_WITNESS_ORGAN.md)

## 10. Activation Order

**Batch:** `alt8-summon-wave-2026-06` — order **2** (after witness organ)

**Depends on:** `continuity_witness_organ` concept; Nova narrative proof bundles

**Minimal invariants:**

- Read-only v1 — no write path from continuity organ
- Continuity questions frozen to doing/done/toward
- Non-authority invariant preserved
