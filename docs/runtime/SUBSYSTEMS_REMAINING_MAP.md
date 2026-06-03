# Subsystems Remaining Map

Living operator map for genome queue, partial→live families, and blocked/dormant work.
Updated for **Release 29** (`alt29-summon-wave-2026-06`, `v1.25.0`).

## Genome queue

| Item | State |
|------|--------|
| Summon gene backlog | **Empty** — 170 governed genomes (169 post–Release 28 + `media_processor_bridge_organ`) |
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
| Execution (Alt29) | Bridge actions + `story_forge_execution_layer` in coherence **v1.24** |
| Stubs | `text_to_3d_world_lane` returns `not_configured`; world pack inspect read-only |

## Blocked / dormant (unchanged)

Per [AAIS_SUBSYSTEM_SPEC.md](./AAIS_SUBSYSTEM_SPEC.md) §4: OTEM execution expansion, standalone ARIS service, Dreamspace — not in Alt29 scope.

## Coherence

- Runtime schema: `operator_cognition_coherence_fabric.v1.24`
- Flags: `story_forge_execution_bundle_aligned`, `integration_universal_bundle_aligned`

## Gates

```bash
make alt29-gate alt29-1-gate alt29-2-gate alt29-governed-gate
```
