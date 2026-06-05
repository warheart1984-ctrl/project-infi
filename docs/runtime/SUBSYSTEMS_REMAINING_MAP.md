# Subsystems Remaining Map

Living operator map for genome queue, partial→live families, and blocked/dormant work.
Updated for **Release 30.1** (`alt30-summon-wave-2026-06`, `v1.26.1`).

## Genome queue

| Item | State |
|------|--------|
| Summon gene backlog | **Empty** — **178 governed** genomes (Release 30 five-pack + Alt-13 wave promotions) |
| Release 30 five-pack | **Governed** — `coding_organs_stack`, `otem_execution_substrate`, `aris_standalone_service`, `dreamspace_organ`, `media_processor_family` |
| Release 28 six-pack | **Governed** — promoted at Alt28; execution layer at Alt29 |

## Partial → live (§6 families — Release 29)

| Governed gene(s) | Release 29 outcome |
|------------------|-------------------|
| `jarvis_memory_board`, `memory_path_governance_organ` | Chat/memory API paths use `memory_enforcer`; universal proof |
| `capability_service_bridge`, `capability_module_organ` | Unregistered bridge actions rejected; Story Forge + media routes registered |
| `governed_direct_pipeline` | Chat hot path uses `build_governed_turn_pipeline`; transport proof |
| `perception_gateway_organ` | `route_perception_entry()` for document vision (+ spatial/mystic stubs) |

Proof bundle: [INTEGRATION_UNIVERSAL_BUNDLE_V1_PROOF.md](../proof/platform/INTEGRATION_UNIVERSAL_BUNDLE_V1_PROOF.md)

## Release 30 (OTEM + posture)

| Governed gene(s) | Release 30 outcome |
|------------------|-------------------|
| `otem_execution_substrate`, `coding_organs_stack` | OTEM execution approval bridge; workflow approvals ingress |
| `aris_standalone_service`, `dreamspace_organ`, `media_processor_family` | Governed posture aligned at Alt30 |

## Story Forge depth

| Layer | State |
|-------|--------|
| Status-only (Alt28) | Six organs — governed status APIs |
| Execution (Alt29) | Bridge actions + `story_forge_execution_layer` in coherence **v1.24** |
| Stubs | `text_to_3d_world_lane` returns `not_configured`; world pack inspect read-only |

## Blocked / dormant (unchanged)

Per [AAIS_SUBSYSTEM_SPEC.md](./AAIS_SUBSYSTEM_SPEC.md) §4: OTEM execution **persistence phase 2** — deferred at v1.26.1.

## Coherence

- Runtime schema: `operator_cognition_coherence_fabric.v1.24`
- Flags: `story_forge_execution_bundle_aligned`, `integration_universal_bundle_aligned`

## Gates

```bash
make alt30-governed-gate v1.26.1-gate
make alt29-governed-gate   # Release 29 historical proof (170 genomes)
```
