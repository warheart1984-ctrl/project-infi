# Game Front Door

CISIV stage: **concept**

Status: pending — Release 28 (`alt28-summon-wave-2026-06`).

## 1. Purpose

Read-only /pipeline game front-door posture.

Wraps: [`external/story_forge/src/story_forge/engine.py`](../../external/story_forge/src/story_forge/engine.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths beyond governed boundary
- No broad direct provider use outside capability_service_bridge

## 4. Subsystem Contract

Schema: [schemas/game_front_door_organ.v1.json](./schemas/game_front_door_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-GFD-01` |
| `status_summary` | Bounded subsystem snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/game-front-door/status` — read-only status
- Runtime module per MVP plan

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required subsystem fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/storyforge/GAME_FRONT_DOOR_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | Runtime status surface |
| Implementation | API route + gate |
| Verification | V1 proof + subsystem gate |

## 9. Related

- [STORYFORGE_CANONICAL.md](../../subsystems/storyforge/STORYFORGE_CANONICAL.md) §7
- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Release:** `alt28-summon-wave-2026-06` — order **4**

**Depends on:** `story_forge_lane_organ`, `story_forge_launcher_organ`, `text_game_to_video_organ`
