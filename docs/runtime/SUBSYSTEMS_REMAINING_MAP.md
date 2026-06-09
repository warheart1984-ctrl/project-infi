# Subsystems Remaining Map

Living operator map for genome queue, partial→live families, and blocked/dormant work.
Updated for **Release 29** (`alt29-summon-wave-2026-06`, `v1.25.0`).

## Genome queue

| Item | State |
|------|--------|
| Summon gene backlog | **Empty** — 179 governed genomes (post–Release 29–30 growth; floor ≥170 for Alt29 gates) |
| Release 28 six-pack | **Governed** — promoted at Alt28; execution layer at Alt29 |

## Partial → live (§6 families — Release 29)

| Governed gene(s) | Release 29 outcome |
|------------------|-------------------|
| `jarvis_memory_board`, `memory_path_governance_organ` | Chat/memory API paths use `memory_enforcer`; universal proof |
| `capability_service_bridge`, `capability_module_organ` | Unregistered bridge actions rejected; Story Forge + media routes registered |
| `governed_direct_pipeline` | Chat hot path uses `build_governed_turn_pipeline`; transport proof |
| `perception_gateway_organ` | `route_perception_entry()` for document vision (+ spatial/mystic stubs) |

Proof bundle: [INTEGRATION_UNIVERSAL_BUNDLE_V1_PROOF.md](../proof/platform/INTEGRATION_UNIVERSAL_BUNDLE_V1_PROOF.md)

## Story Forge depth

| Layer | State |
|-------|--------|
| Status-only (Alt28) | Six organs — governed status APIs |
| Execution (Alt29–34) | Bridge actions + execution layer; movie/video/world-pack lanes execute with `operator_ack` |
| text_to_3d_world_lane | Live deterministic pipeline (Release 34) |

Phase 4 kickoff proof: [STORY_FORGE_PHASE4_KICKOFF_V1_PROOF.md](../proof/platform/STORY_FORGE_PHASE4_KICKOFF_V1_PROOF.md)

## Blocked / dormant (unchanged)

Per [AAIS_SUBSYSTEM_SPEC.md](./AAIS_SUBSYSTEM_SPEC.md) §4: OTEM execution expansion, Dreamspace — not in Alt29 scope.

**Standalone ARIS** — implementation blocked until [ARIS_STANDALONE_ADMISSION_SPEC.md](../contracts/ARIS_STANDALONE_ADMISSION_SPEC.md) criteria are proven (embedded ARIS remains live). Admission spec filed 2026-06-08; service build may proceed under spec checklist.

## Coherence

- Runtime schema: `operator_cognition_coherence_fabric.v1.24`
- Flags: `story_forge_execution_bundle_aligned`, `integration_universal_bundle_aligned`

## Gates

```bash
make alt29-gate alt29-1-gate alt29-2-gate alt29-governed-gate
```
