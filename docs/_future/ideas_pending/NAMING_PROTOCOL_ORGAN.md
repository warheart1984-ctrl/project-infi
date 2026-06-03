# Naming Protocol Subsystem

CISIV stage: **concept**

Status: pending — Release 22 (`alt22-summon-wave-2026-06`).

## 1. Purpose

Read-only Codex/Cursor naming protocol lint posture (Wave 0).

Wraps: [`tools/naming_protocol_lint.py`](../../tools/naming_protocol_lint.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via subsystem API
- No MP-X apply without existing mutation-path gates

## 4. Subsystem Contract

Schema: [schemas/naming_protocol_organ.v1.json](./schemas/naming_protocol_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-NPR-01` |
| `status_summary` | Bounded subsystem snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/naming-protocol/status` — read-only status
- `src/naming_protocol_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required subsystem fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/NAMING_PROTOCOL_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/naming_protocol_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + subsystem gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [AAIS_META_LINGUISTIC_GOVERNANCE.md](../../contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md)
- [AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../../contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md)

## 10. Activation Order

**Release:** `alt22-summon-wave-2026-06` — order **1**

**Depends on:** `module_governance_organ`, `governance_layer_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-NPR-01`
