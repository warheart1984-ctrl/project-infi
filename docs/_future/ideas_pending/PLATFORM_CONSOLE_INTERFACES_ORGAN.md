# Platform Console Interfaces Subsystem

CISIV stage: **concept**

Status: pending — Release 20 (`alt20-summon-wave-2026-06`).

## 1. Purpose

Read-only platform console UI cluster posture.

Wraps: [`frontend/src/pages/PlatformConsole.jsx`](../../frontend/src/pages/PlatformConsole.jsx).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via subsystem API

## 4. Subsystem Contract

Schema: [schemas/platform_console_interfaces_organ.v1.json](./schemas/platform_console_interfaces_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-PCI-01` |
| `status_summary` | Bounded subsystem snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/platform-console-interfaces/status` — read-only status
- `src/platform_console_interfaces_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required subsystem fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/PLATFORM_CONSOLE_INTERFACES_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/platform_console_interfaces_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + subsystem gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [JARVIS_PROTOCOL.md](../../contracts/JARVIS_PROTOCOL.md)

## 10. Activation Order

**Release:** `alt20-summon-wave-2026-06` — order **7**

**Depends on:** `api_gateway_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-PCI-01`
