# Nova Landing Surface Organ

CISIV stage: **concept**

Status: pending — Alt-19 summon wave `alt19-summon-wave-2026-06`.

## 1. Purpose

Read-only Nova landing surface posture.

Wraps: [`frontend/src/pages/NovaLandingPage.jsx`](../../frontend/src/pages/NovaLandingPage.jsx).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via organ API

## 4. Organ Contract

Schema: [schemas/nova_landing_surface_organ.v1.json](./schemas/nova_landing_surface_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-NLS-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/nova-landing-surface/status` — read-only status
- `src/nova_landing_surface_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/NOVA_LANDING_SURFACE_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/nova_landing_surface_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [JARVIS_PROTOCOL.md](../../contracts/JARVIS_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt19-summon-wave-2026-06` — order **7**

**Depends on:** `nova_face_organ`, `jarvis_console_surface_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-NLS-01`
