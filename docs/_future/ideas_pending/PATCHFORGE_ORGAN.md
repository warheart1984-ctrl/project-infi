# Patchforge Organ

CISIV stage: **concept**

Status: pending — Alt-11 summon wave `alt11-summon-wave-2026-06`.

## 1. Purpose

Read-only PatchForge proposal/preview-only attestation.

Wraps: [`src/patchforge.py`](../../src/patchforge.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous escalation or repo mutation
- No replacement of underlying governed subsystems

## 4. Organ Contract

Schema: [schemas/patchforge_organ.v1.json](./schemas/patchforge_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-PF-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/patchforge/status` — read-only status
- `src/patchforge_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/PATCHFORGE_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/patchforge_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [AAIS_TRACING_PROTOCOL.md](../../contracts/AAIS_TRACING_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt11-summon-wave-2026-06` — order **7**

**Depends on:** `tracing_spine_organ`, `capability_module_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-PF-01`
