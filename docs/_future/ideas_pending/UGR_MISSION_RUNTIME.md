# UGR Mission Runtime

CISIV stage: **concept**

Status: pending — not yet integrated into active AAIS doc tree or backed by runtime.

## 1. Purpose

**Mythic:** UGR Mission Runtime — executes governed missions, steps for promotion and adoption of discovered subsystems, and feeds attribution back into the reward chain.

**Engineering:** `MissionRuntimeEngine` — mission board integration, step execution, receipt of governance signals, and adoption event emission for rewards.

## 2. Authority And Precedence

Defers to UGR rewards contract for attribution; uses mission board and Project Infi where repo/governance mutations are involved.

## 3. Non-Goals

Does not originate rewards (hands off to reward engine after adoption).

## 4. Core Contract

Schema: [schemas/ugr_mission_runtime.v1.json](./schemas/ugr_mission_runtime.v1.json)

## 5-7. Implementation

See src/ugr/mission/ + mission board surfaces.

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Mission execution + adoption attribution | `proven` | src/ugr/mission + tests + genomes |

Target proof packet: docs/proof/ugr/UGR_MISSION_RUNTIME_V1_PROOF.md

## 9. CISIV Path

As siblings in UGR batch.

## 10. Related

- Reward engine, discovery
- Genome: ugr_mission_runtime.genome.v1.json

## 11. Activation Order Notes

Depends on discovery for subsystem ids; feeds reward engine.
