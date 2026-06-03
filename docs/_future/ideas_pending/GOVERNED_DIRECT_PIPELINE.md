# Governed Direct Pipeline

CISIV stage: **concept**

Status: pending — Release 27 (`alt27-summon-wave-2026-06`).

## 1. Purpose

Read-only governed direct turn pipeline trace posture.

Wraps: [`src/governed_direct_pipeline.py`](../../src/governed_direct_pipeline.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via subsystem API

## 4. Subsystem Contract

Schema: [schemas/governed_direct_pipeline.v1.json](./schemas/governed_direct_pipeline.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-GDP-01` |
| `status_summary` | Bounded subsystem snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/pipeline/{turn_id}` — read-only status
- Runtime module per MVP plan

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required subsystem fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/GOVERNED_DIRECT_PIPELINE_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | Runtime status surface |
| Implementation | API route + gate |
| Verification | V1 proof + subsystem gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [AAIS_META_LINGUISTIC_GOVERNANCE.md](../../contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md)

## 10. Activation Order

**Release:** `alt27-summon-wave-2026-06` — order **5**

**Depends on:** `capability_service_bridge`, `jarvis_memory_board`
