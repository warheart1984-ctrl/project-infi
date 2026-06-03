# Intent Agency Organ

CISIV stage: **concept**

Status: pending — Alt-8 summon wave `alt8-summon-wave-2026-06`.

## 1. Purpose

Formalize **Nova Intent / Agency** posture from
[`src/cog_runtime/intent_core.py`](../../src/cog_runtime/intent_core.py) as a governed Alt-8
organ: read-only agency note, tensions, and commitment summary without overriding
Jarvis authority.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Subordinate to Jarvis routing;
intent consults; it does not authorize execution.

## 3. Non-Goals

- No autonomous commitment promotion without Jarvis authorize
- No replacement for full intent store turn processing in v1
- No coherence projection routing changes

## 4. Organ Contract

Schema: [schemas/intent_agency_organ.v1.json](./schemas/intent_agency_organ.v1.json)

| Field | Role |
|-------|------|
| `agency_note` | Bounded agency summary |
| `active_tension_count` | In-tension commitment count |
| `agency_claim_posture` | Claim label coverage |

## 5. Runtime (Proposed)

- `GET /api/jarvis/intent-agency/status` — read-only intent/agency snapshot
- `src/intent_agency_organ.py` — wraps intent evidence fixtures

## 6. Failsafe

Missing intent artifact returns idle snapshot with `claim_label: asserted`.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns agency snapshot | `none_yet` | Requires MVP |
| Session-reset fixture survival | `none_yet` | Requires gate |

Target proof packet: `docs/proof/cognitive_runtime/INTENT_AGENCY_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/intent_agency_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + `make intent-agency-gate` |

## 9. Related

- [NOVA_INTENT_CORE.md](../../runtime/NOVA_INTENT_CORE.md)
- [INTENT_AGENCY_V1_PROOF_BUNDLE.md](../../proof/cognitive_runtime/INTENT_AGENCY_V1_PROOF_BUNDLE.md)
- [NARRATIVE_CONTINUITY_ORGAN.md](./NARRATIVE_CONTINUITY_ORGAN.md)

## 10. Activation Order

**Batch:** `alt8-summon-wave-2026-06` — order **3** (after narrative continuity organ)

**Depends on:** `narrative_continuity_organ` concept; Alt-7.2 coherence fabric

**Minimal invariants:**

- Read-only v1 — no write path from intent agency organ
- Claim postures limited to asserted/proven/rejected
- Agency preservation constitutional values respected in snapshot
