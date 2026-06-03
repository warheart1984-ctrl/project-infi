# Subsystem Genome Registry

SSP Alt-4 DNA records for AAIS subsystem families.

Meta-schema: [schemas/subsystem_genome.v1.json](../../schemas/subsystem_genome.v1.json)

Contract: [docs/contracts/AAIS_SUBSYSTEM_GENOME.md](../../docs/contracts/AAIS_SUBSYSTEM_GENOME.md)

## Gate

```bash
make genome-gate
make alt4-gate
make alt5-gate
make alt6-gate
make alt6-governed-gate
make alt7-gate
make alt7-governed-gate
```

## Registered Genomes

| Gene | Stage | File |
|------|-------|------|
| `cisiv_operator_lineage_console` | governed | [cisiv_operator_lineage_console.genome.v1.json](./cisiv_operator_lineage_console.genome.v1.json) |
| `forensic_triangulation` | governed | [forensic_triangulation.genome.v1.json](./forensic_triangulation.genome.v1.json) |
| `narrative_trust_pack` | governed | [narrative_trust_pack.genome.v1.json](./narrative_trust_pack.genome.v1.json) |
| `recipe_module` | governed | [recipe_module.genome.v1.json](./recipe_module.genome.v1.json) |
| `imagine_generator` | governed | [imagine_generator.genome.v1.json](./imagine_generator.genome.v1.json) |
| `human_voice_extraction` | governed | [human_voice_extraction.genome.v1.json](./human_voice_extraction.genome.v1.json) |
| `safety_envelope_organ` | governed | [safety_envelope_organ.genome.v1.json](./safety_envelope_organ.genome.v1.json) |
| `operator_profile_organ` | governed | [operator_profile_organ.genome.v1.json](./operator_profile_organ.genome.v1.json) |
| `reflection_runtime_organ` | governed | [reflection_runtime_organ.genome.v1.json](./reflection_runtime_organ.genome.v1.json) |
| `memory_runtime_organ` | governed | [memory_runtime_organ.genome.v1.json](./memory_runtime_organ.genome.v1.json) |
| `capability_service_bridge` | governed | [capability_service_bridge.genome.v1.json](./capability_service_bridge.genome.v1.json) |
| `jarvis_memory_board` | governed | [jarvis_memory_board.genome.v1.json](./jarvis_memory_board.genome.v1.json) |
| `governed_direct_pipeline` | governed | [governed_direct_pipeline.genome.v1.json](./governed_direct_pipeline.genome.v1.json) |
| `adaptive_lane_organ` | governed | [adaptive_lane_organ.genome.v1.json](./adaptive_lane_organ.genome.v1.json) |
| `operator_cognition_coherence_fabric` | governed | [operator_cognition_coherence_fabric.genome.v1.json](./operator_cognition_coherence_fabric.genome.v1.json) |
| `continuity_witness_organ` | governed | [continuity_witness_organ.genome.v1.json](./continuity_witness_organ.genome.v1.json) |
| `narrative_continuity_organ` | governed | [narrative_continuity_organ.genome.v1.json](./narrative_continuity_organ.genome.v1.json) |
| `intent_agency_organ` | governed | [intent_agency_organ.genome.v1.json](./intent_agency_organ.genome.v1.json) |
| `phase_gate_organ` | governed | [phase_gate_organ.genome.v1.json](./phase_gate_organ.genome.v1.json) |
| `realtime_event_cause_predictor_organ` | governed | [realtime_event_cause_predictor_organ.genome.v1.json](./realtime_event_cause_predictor_organ.genome.v1.json) |
| `invariant_engine_organ` | governed | [invariant_engine_organ.genome.v1.json](./invariant_engine_organ.genome.v1.json) |
| `verification_gate_organ` | governed | [verification_gate_organ.genome.v1.json](./verification_gate_organ.genome.v1.json) |
| `memory_path_governance_organ` | governed | [memory_path_governance_organ.genome.v1.json](./memory_path_governance_organ.genome.v1.json) |
| `knowledge_authority_organ` | governed | [knowledge_authority_organ.genome.v1.json](./knowledge_authority_organ.genome.v1.json) |
| `scorpion_bridge_organ` | governed | [scorpion_bridge_organ.genome.v1.json](./scorpion_bridge_organ.genome.v1.json) |
| `mechanic_handoff_organ` | governed | [mechanic_handoff_organ.genome.v1.json](./mechanic_handoff_organ.genome.v1.json) |
| `forensic_triangulation_organ` | governed | [forensic_triangulation_organ.genome.v1.json](./forensic_triangulation_organ.genome.v1.json) |
| `immune_observe_organ` | governed | [immune_observe_organ.genome.v1.json](./immune_observe_organ.genome.v1.json) |
| `policy_gate_organ` | governed | [policy_gate_organ.genome.v1.json](./policy_gate_organ.genome.v1.json) |
| `predictor_immune_bridge_organ` | governed | [predictor_immune_bridge_organ.genome.v1.json](./predictor_immune_bridge_organ.genome.v1.json) |

## Adding a Genome

On SSP summon (Step 7), create `<gene>.genome.v1.json` at `stage: concept` with
empty `runtime.surface` and `proof.posture: asserted`.

Update this table and run `make genome-gate`.
