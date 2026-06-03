# Changelog

All notable changes to the **AAIS Python runtime and operator surfaces** are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

CoGOS ISO releases are tracked separately — see [docs/releases/README.md](docs/releases/README.md).

## [Unreleased]

### Added

- (none yet)

## [1.24.0] - 2026-06-03 — Release 28 Story Forge Expansion Fabric

**Release 28** (`alt28-summon-wave-2026-06`) — six Story Forge expansion subsystems; Coherence Layer v1.23; frontier model provider catalog; chat latency caches; genome lineage symmetry fixes for boot.

### Added

- **Release 28.0** — `story_forge_launcher_organ`, `movie_renderer_lane_organ`, `text_game_to_video_organ`, `game_front_door_organ`, `text_to_3d_world_lane_organ`, `world_pack_lane_organ`; status APIs; `make alt28-gate`; `tools/governance/alt28_promote_mvp.py`
- **Release 28.1** — Coherence Layer v1.23 + `story_forge_expansion_layer`, `story_forge_expansion_bundle_aligned`; `make alt28-1-gate`
- **Release 28.2** — `STORYFORGE_EXPANSION_BUNDLE_V1_PROOF`; `make alt28-2-gate`
- **Governed promotion** — `tools/governance/alt28_promote_governed.py`; `make alt28-governed-gate`
- **Frontier providers** — twelve OpenAI-compatible adapters (OpenAI, Google Gemini, Mistral, DeepSeek, xAI, Groq, Together, Fireworks, Perplexity, **NVIDIA Nemotron 3**, Azure OpenAI, Moonshot, AI21); catalog in `src/providers/frontier_catalog.py`
- **Runtime caches** — `AAIS_COHERENCE_FABRIC_CACHE_SEC`, `AAIS_GOVERNED_PIPELINE_CACHE_SEC`, `AAIS_SLINGSHOT_CACHE_SEC` (Slingshot frame/packet JSON)

### Changed

- Schema registry: **169** subsystem genomes at MVP batch (163 prior governed + 6 Release 28)
- `operator_cognition_coherence_fabric` runtime schema → v1.23
- Genome `parents` symmetry for `capability_service_bridge`, `jarvis_memory_board`, `recipe_module`, and related lineage (fixes `aais start` genome-gate boot failures)
- Provider registry lists all frontier adapters disabled until API keys are set (see `.env.example`)

### Verification (v1.24.0)

```bash
python tools/governance/_alt28_ssp_bootstrap.py
python tools/governance/_alt28_coherence_v123.py
make alt28-gate alt28-1-gate alt28-2-gate alt28-governed-gate
python -m pytest tests/test_story_forge_launcher_organ.py tests/test_frontier_catalog.py -q
```

[1.24.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.24.0

## [1.23.0] - 2026-06-03 — Release 27 CISIV Early Ideas Fabric

**Release 27** — nine governed subsystems batch-stamped at `alt27-summon-wave-2026-06`; Coherence Layer v1.22 with CISIV/bridge/creative trust layers; Wave 18 early ideas bundle aligned with operational closure.

### Added

- **Release 27.0** — `cisiv_operator_lineage_console`, `forensic_triangulation`, `capability_service_bridge`, `jarvis_memory_board`, `governed_direct_pipeline`, `recipe_module`, `imagine_generator`, `narrative_trust_pack`, `human_voice_extraction`; `make alt27-gate`; `tools/governance/alt27_promote_mvp.py`
- **Release 27.1** — Coherence Layer v1.22 + `cisiv_lineage_triangulation_layer`, `constitutional_bridge_layer`, `creative_trust_chain_layer`, `cisiv_early_ideas_bundle_aligned`; `make alt27-1-gate`
- **Release 27.2** — `CISIV_EARLY_IDEAS_BUNDLE_V1_PROOF`; `make alt27-2-gate`
- **Governed promotion** — `tools/governance/alt27_promote_governed.py`; `make alt27-governed-gate`

### Changed

- Schema registry: **163 governed** subsystem schemas (unchanged count; Release 27 batch formalization)
- `operator_cognition_coherence_fabric` runtime schema → v1.22
- `check_alt24_closure` / `check_alt25_governed_eligibility` / `check_alt26_governed_eligibility` accept coherence v1.19–v1.22 cumulatively

### Verification (v1.23.0)

```bash
make alt27-gate alt27-1-gate alt27-2-gate alt27-governed-gate
python tools/governance/_alt27_coherence_v122.py
python -m pytest tests/test_operator_cognition_coherence_fabric.py::test_alt27_early_ideas_layers_at_v122 -q
```

[1.23.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.23.0

## [1.22.0] - 2026-06-03 — Release 26 Operational Closure

**Release 26** — three read-only subsystems at governed; Coherence Layer v1.21 with operator day and retention history layers; Wave 17 operational closure; naming-gate clean (0 warnings).

### Added

- **Release 26.0** — `linguistic_governance_day_organ`, `linguistic_work_order_history_organ`, `linguistic_attestation_history_organ`; status APIs; `make alt26-gate`; `tools/governance/alt26_promote_mvp.py`
- **Release 26.1** — Coherence Layer v1.21 + `linguistic_operator_day_layer`, `linguistic_retention_history_layer`, `linguistic_operational_closure_aligned`; `make alt26-1-gate`
- **Release 26.2** — `LINGUISTIC_OPERATIONAL_CLOSURE_V1_PROOF`; `make alt26-2-gate`
- **Governed promotion** — `tools/governance/alt26_promote_governed.py`; `make alt26-governed-gate`
- **Codex headers** — `tools/governance/apply_engineering_file_headers.py`; `# Engineering:` / `# Mythic:` on subsystem shells
- **Grandfather registry** — 34 linguistic `*_organ.py` paths in `legacy_engineering_aliases.v1.json`

### Changed

- Schema registry: **163 governed** subsystem schemas (160 prior + 3 Release 26)
- `operator_cognition_coherence_fabric` runtime schema → v1.21
- `check_alt24_closure` / `check_alt25_governed_eligibility` accept coherence v1.19–v1.21 for cumulative stack gates

### Verification (v1.22.0)

```bash
python tools/naming_protocol_lint.py
python -m src.governance_organs.linguistic_governance_engine --gate
python tools/governance/check_linguistic_governance_stack_gate.py
python tools/governance/check_alt25_governed_eligibility.py
python tools/governance/check_alt26_governed_eligibility.py
```

[1.22.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.22.0

## [1.21.0] - 2026-06-03 — Release 25 Governed Linguistic Lifecycle Fabric

**Release 25** — nine read-only subsystems at governed; Coherence Layer v1.20 with execution, artifact, and promotion layers; Wave 16 lifecycle fabric.

### Added

- **Release 25.0** — nine Release 25 organs (forecast archive through governed lifecycle fabric); `make alt25-gate`; `tools/governance/alt25_promote_mvp.py`
- **Release 25.1** — Coherence Layer v1.20 + governed lifecycle layers; `make alt25-1-gate`
- **Release 25.2** — `GOVERNED_LINGUISTIC_LIFECYCLE_V1_PROOF`; `make alt25-2-gate`
- **Governed promotion** — `tools/governance/alt25_promote_governed.py`; `make alt25-governed-gate`

### Changed

- Schema registry: **160 governed** subsystem schemas (151 prior + 9 Release 25)
- `operator_cognition_coherence_fabric` schema ref → v1.20

### Verification (v1.21.0)

```bash
make alt25-gate alt25-1-gate alt25-2-gate alt25-governed-gate
```

[1.21.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.21.0

## [1.20.0] - 2026-06-03 — Release 24 Attested Linguistic Closed-Loop

**Release 24** — four read-only subsystems at governed; Coherence Layer v1.19 with calibration, queue, and attestation layers; Wave 14 attestation and work-order engines.

### Added

- **Release 24.0** — `linguistic_forecast_calibration_organ`, `linguistic_governance_queue_organ`, `linguistic_full_governance_cycle_organ`, `linguistic_governance_attestation_organ`; status APIs; `make alt24-gate`; `tools/governance/alt24_promote_mvp.py`
- **Release 24.1** — Coherence Layer v1.19 + `linguistic_calibration_layer`, `linguistic_governance_queue_layer`, `linguistic_attestation_layer`, `linguistic_attested_closed_loop_aligned`; `make alt24-1-gate`
- **Release 24.2** — `ATTESTED_LINGUISTIC_CLOSED_LOOP_V1_PROOF`; `make alt24-2-gate`
- **Governed promotion** — `tools/governance/alt24_promote_governed.py`; `make alt24-governed-gate`
- **Wave 14 engines** — forecast archive, work-order sync, unified attestation digest, cadence gates

### Changed

- Schema registry: **151 governed** subsystem schemas (147 prior + 4 Release 24)
- `operator_cognition_coherence_fabric` schema ref → v1.19

### Verification (v1.20.0)

```bash
make alt24-gate alt24-1-gate alt24-2-gate alt24-governed-gate
make linguistic-governance-attestation
python -m pytest tests/test_linguistic_forecast_calibration_organ.py tests/test_linguistic_governance_queue_organ.py tests/test_linguistic_full_governance_cycle_organ.py tests/test_linguistic_governance_attestation_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.20.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.20.0

## [1.19.0] - 2026-06-03 — Release 23 Predictive Linguistic Cycle Fabric

**Release 23** — nine read-only subsystems at governed; Coherence Layer v1.18 with forecast, predictive cycle, and governance cycle layers; Wave 11–12 predictive stack.

### Added

- **Release 23.0** — `linguistic_drift_forecast_organ`, `linguistic_preemptive_remediation_organ`, `linguistic_predictive_governance_organ`, `linguistic_predictive_cycle_history_organ`, `linguistic_governance_cycle_organ`, `linguistic_governance_cycle_history_organ`, `linguistic_forecast_consumption_organ`, `linguistic_cycle_optimization_organ`, `linguistic_closed_loop_fabric_organ`; status APIs; `make alt23-gate`
- **Release 23.1** — Coherence Layer v1.18 + predictive/cycle layers; `make alt23-1-gate`
- **Release 23.2** — `PREDICTIVE_LINGUISTIC_CYCLE_V1_PROOF`; `make alt23-2-gate`
- **Governed promotion** — `tools/governance/alt23_promote_governed.py`; `make alt23-governed-gate`

### Changed

- Schema registry: **147 governed** subsystem schemas (138 prior + 9 Release 23)
- `operator_cognition_coherence_fabric` schema ref → v1.18

### Verification (v1.19.0)

```bash
make alt23-gate alt23-1-gate alt23-2-gate alt23-governed-gate
make linguistic-predictive-cycle
```

[1.19.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.19.0

## [1.18.0] - 2026-06-03 — Release 22 Meta-Linguistic Governance Fabric

**Release 22** — nine read-only subsystems at governed; Coherence Layer v1.17 with naming protocol, linguistic mutation, and meta orchestration layers; meta-linguistic governance engine (Waves 0–10).

### Added

- **Release 22.0** — `naming_protocol_organ`, `naming_genome_organ`, `linguistic_mutation_organ`, `mythic_engineering_translator_organ`, `linguistic_drift_predictor_organ`, `linguistic_lineage_viz_organ`, `linguistic_remediation_organ`, `linguistic_cascade_organ`, `meta_linguistic_governance_organ`; status APIs; `make alt22-gate`; `tools/governance/alt22_promote_mvp.py`
- **Release 22.1** — Coherence Layer v1.17 + `naming_protocol_layer`, `linguistic_mutation_layer`, `meta_linguistic_orchestration_layer`, `meta_linguistic_governance_aligned`; `make alt22-1-gate`
- **Release 22.2** — `META_LINGUISTIC_GOVERNANCE_V1_PROOF`; `make alt22-2-gate`
- **Governed promotion** — `tools/governance/alt22_promote_governed.py`; `make alt22-governed-gate`
- **Meta-linguistic stack** — naming protocol lint, genome validator, mutation/remediation/cascade engines, drift predictor, lineage viz, `make meta-linguistic-gate`

### Changed

- Schema registry: **138 governed** subsystem schemas (129 prior + 9 Release 22)
- `operator_cognition_coherence_fabric` schema ref → v1.17

### Verification (v1.18.0)

```bash
make alt22-gate alt22-1-gate alt22-2-gate alt22-governed-gate
make meta-linguistic-gate
python -m pytest tests/test_naming_protocol_organ.py tests/test_naming_genome_organ.py tests/test_linguistic_mutation_organ.py tests/test_mythic_engineering_translator_organ.py tests/test_linguistic_drift_predictor_organ.py tests/test_linguistic_lineage_viz_organ.py tests/test_linguistic_remediation_organ.py tests/test_linguistic_cascade_organ.py tests/test_meta_linguistic_governance_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.18.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.18.0

## [1.17.0] - 2026-06-03 — Release 21 Creative Runtime V9/V10 Fabric

**Release 21** — nine read-only subsystems at governed; Coherence Layer v1.16 with creative core, V9 creative, and V10 creative runtime layers.

### Added

- **Release 21.0** — `creative_core_runtime_organ`, `v9_core_organ`, `v9_runtime_organ`, `v10_core_organ`, `v10_runtime_organ`, `v10_action_engine_organ`, `creative_capability_bridge_organ`, `creative_operator_handoff_organ`, `creative_console_interface_organ`; status APIs; `make alt21-gate`; `tools/governance/alt21_promote_mvp.py`
- **Release 21.1** — Coherence Layer v1.16 + `creative_core_layer`, `v9_creative_layer`, `v10_creative_layer`, `creative_runtime_v9_v10_aligned`; `make alt21-1-gate`
- **Release 21.2** — `CREATIVE_RUNTIME_V9_V10_V1_PROOF`; `make alt21-2-gate`
- **Governed promotion** — `tools/governance/alt21_promote_governed.py`; `make alt21-governed-gate`

### Changed

- Schema registry: **129 governed** subsystem schemas (120 prior + 9 Release 21)
- `operator_cognition_coherence_fabric` schema ref → v1.16

### Verification (v1.17.0)

```bash
make alt21-gate alt21-1-gate alt21-2-gate alt21-governed-gate
python -m pytest tests/test_creative_core_runtime_organ.py tests/test_v9_core_organ.py tests/test_v9_runtime_organ.py tests/test_v10_core_organ.py tests/test_v10_runtime_organ.py tests/test_v10_action_engine_organ.py tests/test_creative_capability_bridge_organ.py tests/test_creative_operator_handoff_organ.py tests/test_creative_console_interface_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.17.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.17.0

## [1.16.0] - 2026-06-03 — Release 20 Operator Workspace & Extended Interfaces

**Release 20** — nine read-only subsystems at governed; Coherence Layer v1.15 with workspace/memory, hygiene/blueprint, and extended operator interface layers.

### Added

- **Release 20.0** — `memory_smith_organ`, `operator_workspace_organ`, `jarvis_runs_organ`, `state_hygiene_organ`, `blueprint_posture_organ`, `workflow_interfaces_organ`, `platform_console_interfaces_organ`, `operator_console_interface_organ`, `nova_workspace_interface_organ`; status APIs; `make alt20-gate`; `tools/governance/alt20_promote_mvp.py`
- **Release 20.1** — Coherence Layer v1.15 + `workspace_memory_layer`, `hygiene_blueprint_layer`, `extended_operator_interface_layer`, `operator_workspace_interfaces_aligned`; `make alt20-1-gate`
- **Release 20.2** — `OPERATOR_WORKSPACE_INTERFACES_V1_PROOF`; `make alt20-2-gate`
- **Governed promotion** — `tools/governance/alt20_promote_governed.py`; `make alt20-governed-gate`
- **Terminology** — Project Infinity glossary in README and [AAIS_SSP_PROTOCOL.md](docs/contracts/AAIS_SSP_PROTOCOL.md) (Subsystem, Schema, Interface, Layer, Coherence Layer, Release)

### Changed

- Schema registry: **120 governed** subsystem schemas (111 prior + 9 Release 20)
- `operator_cognition_coherence_fabric` schema ref → v1.15

### Verification (v1.16.0)

```bash
make alt20-gate alt20-1-gate alt20-2-gate alt20-governed-gate
python -m pytest tests/test_memory_smith_organ.py tests/test_operator_workspace_organ.py tests/test_jarvis_runs_organ.py tests/test_state_hygiene_organ.py tests/test_blueprint_posture_organ.py tests/test_workflow_interfaces_organ.py tests/test_platform_console_interfaces_organ.py tests/test_operator_console_interface_organ.py tests/test_nova_workspace_interface_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.16.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.16.0

## [1.15.0] - 2026-06-02 — Alt-19 Operator Product Shell Fabric

**Alt-19** — nine read-only organs at governed; coherence fabric v1.14 with product shell, operator surface, and composed runtime posture planes.

### Added

- **Alt-19.0** — `launcher_organ`, `aais_doctor_organ`, `workflow_runtime_organ`, `jarvis_console_surface_organ`, `memory_bank_surface_organ`, `dashboard_surface_organ`, `nova_landing_surface_organ`, `aais_composed_runtime_organ`, `api_gateway_organ`; status APIs; `make alt19-gate`; `tools/governance/alt19_promote_mvp.py`
- **Alt-19.1** — coherence snapshot v1.14 + `product_shell_aligned`, `operator_surface_aligned`, `composed_runtime_aligned`, `operator_product_shell_aligned`; `make alt19-1-gate`
- **Alt-19.2** — `OPERATOR_PRODUCT_SHELL_V1_PROOF`; `make alt19-2-gate`
- **Governed promotion** — `tools/governance/alt19_promote_governed.py`; `make alt19-governed-gate`

### Changed

- Genome registry: **111 governed** subsystem genomes (102 prior + 9 Alt-19)
- `operator_cognition_coherence_fabric` schema ref → v1.14

### Verification (v1.15.0)

```bash
make alt19-gate alt19-1-gate alt19-2-gate alt19-governed-gate
python -m pytest tests/test_launcher_organ.py tests/test_aais_doctor_organ.py tests/test_workflow_runtime_organ.py tests/test_jarvis_console_surface_organ.py tests/test_memory_bank_surface_organ.py tests/test_dashboard_surface_organ.py tests/test_nova_landing_surface_organ.py tests/test_aais_composed_runtime_organ.py tests/test_api_gateway_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.15.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.15.0

## [1.14.0] - 2026-06-02 — Alt-18 Project Infi Law Fabric

**Alt-18** — nine read-only organs at governed; coherence fabric v1.13 with law cycle, turn admission, and governance control posture planes.

### Added

- **Alt-18.0** — `project_infi_state_machine_organ`, `project_infi_law_organ`, `run_ledger_binding_organ`, `chat_turn_governance_organ`, `aais_ul_substrate_organ`, `aris_integration_organ`, `governance_layer_organ`, `security_protocol_organ`, `system_guard_organ`; status APIs; `make alt18-gate`; `tools/governance/alt18_promote_mvp.py`
- **Alt-18.1** — coherence snapshot v1.13 + `law_cycle_aligned`, `turn_admission_aligned`, `governance_control_aligned`, `project_infi_law_aligned`; `make alt18-1-gate`
- **Alt-18.2** — `PROJECT_INFI_LAW_V1_PROOF` + `CHAT_TURN_GOVERNANCE_ORGAN_V1_PROOF` + `GOVERNANCE_LAYER_ORGAN_V1_PROOF`; `make alt18-2-gate`
- **Governed promotion** — `tools/governance/alt18_promote_governed.py`; `make alt18-governed-gate`

### Changed

- Genome registry: **102 governed** subsystem genomes (93 prior + 9 Alt-18)
- `operator_cognition_coherence_fabric` schema ref → v1.13

### Verification (v1.14.0)

```bash
make alt18-gate alt18-1-gate alt18-2-gate alt18-governed-gate
python -m pytest tests/test_project_infi_state_machine_organ.py tests/test_project_infi_law_organ.py tests/test_run_ledger_binding_organ.py tests/test_chat_turn_governance_organ.py tests/test_aais_ul_substrate_organ.py tests/test_aris_integration_organ.py tests/test_governance_layer_organ.py tests/test_security_protocol_organ.py tests/test_system_guard_organ.py tests/test_operator_cognition_coherence_fabric.py tests/test_project_infi_law.py tests/test_chat_turn_governance.py -q
```

[1.14.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.14.0

## [1.13.0] - 2026-06-02 — Alt-17 Authority Shell & Protocol Fabric

**Alt-17** — nine read-only organs at governed; coherence fabric v1.12 with protocol, authority shell, and response integrity posture planes.

### Added

- **Alt-17.0** — `jarvis_protocol_organ`, `reasoning_contract_organ`, `jarvis_reasoning_lane_organ`, `conversation_memory_organ`, `continuity_substrate_organ`, `jarvis_operator_organ`, `anti_drift_organ`, `prompt_assembly_organ`, `output_integrity_organ`; status APIs; `make alt17-gate`; `tools/governance/alt17_promote_mvp.py`
- **Alt-17.1** — coherence snapshot v1.12 + `protocol_aligned`, `authority_shell_aligned`, `response_integrity_aligned`, `authority_protocol_integrity_aligned`; `make alt17-1-gate`
- **Alt-17.2** — `AUTHORITY_PROTOCOL_INTEGRITY_V1_PROOF` + `JARVIS_PROTOCOL_ORGAN_V1_PROOF` + `OUTPUT_INTEGRITY_ORGAN_V1_PROOF`; `make alt17-2-gate`
- **Governed promotion** — `tools/governance/alt17_promote_governed.py`; `make alt17-governed-gate`

### Changed

- Genome registry: **93 governed** subsystem genomes (84 prior + 9 Alt-17)
- `operator_cognition_coherence_fabric` schema ref → v1.12

### Verification (v1.13.0)

```bash
make alt17-gate alt17-1-gate alt17-2-gate alt17-governed-gate
python -m pytest tests/test_jarvis_protocol_organ.py tests/test_reasoning_contract_organ.py tests/test_jarvis_reasoning_lane_organ.py tests/test_conversation_memory_organ.py tests/test_continuity_substrate_organ.py tests/test_jarvis_operator_organ.py tests/test_anti_drift_organ.py tests/test_prompt_assembly_organ.py tests/test_output_integrity_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.13.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.13.0

## [1.12.0] - 2026-06-02 — Alt-16 Factory & Kinetic Fabric

**Alt-16** — nine read-only organs at governed; coherence fabric v1.11 with factory fabrication, contractor lane, and kinetic shell posture planes.

### Added

- **Alt-16.0** — `ai_factory_organ`, `cogos_runtime_bridge_organ`, `wolf_rehydration_organ`, `forge_contractor_organ`, `forge_eval_organ`, `evolve_engine_organ`, `slingshot_organ`, `operator_workbench_organ`, `workflow_shell_organ`; status APIs; `make alt16-gate`; `tools/governance/alt16_promote_mvp.py`
- **Alt-16.1** — coherence snapshot v1.11 + `factory_fabrication_aligned`, `contractor_lanes_aligned`, `kinetic_shell_aligned`, `factory_kinetic_aligned`; `make alt16-1-gate`
- **Alt-16.2** — `FACTORY_KINETIC_V1_PROOF` + `AI_FACTORY_ORGAN_V1_PROOF` + `SLINGSHOT_ORGAN_V1_PROOF`; `make alt16-2-gate`
- **Governed promotion** — `tools/governance/alt16_promote_governed.py`; `make alt16-governed-gate`

### Changed

- Genome registry: **84 governed** subsystem genomes (75 prior + 9 Alt-16)
- `operator_cognition_coherence_fabric` schema ref → v1.11

### Verification (v1.12.0)

```bash
make alt16-gate alt16-1-gate alt16-2-gate alt16-governed-gate
python -m pytest tests/test_ai_factory_organ.py tests/test_cogos_runtime_bridge_organ.py tests/test_wolf_rehydration_organ.py tests/test_forge_contractor_organ.py tests/test_forge_eval_organ.py tests/test_evolve_engine_organ.py tests/test_slingshot_organ.py tests/test_operator_workbench_organ.py tests/test_workflow_shell_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.12.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.12.0

## [1.11.0] - 2026-06-02 — Alt-15 Nova Cortex Lobe & Voice Fabric

**Alt-15** — nine read-only organs at governed; coherence fabric v1.10 with executive/attention, deliberation/planning, and voice/execution posture planes.

### Added

- **Alt-15.0** — `reasoning_executive_organ`, `attention_organ`, `coherence_projection_organ`, `deliberation_organ`, `planning_organ`, `cortex_arcs_organ`, `cognitive_execution_organ`, `speaking_runtime_organ`, `nova_face_organ`; status APIs; `make alt15-gate`; `tools/governance/alt15_promote_mvp.py`
- **Alt-15.1** — coherence snapshot v1.10 + `executive_attention_aligned`, `deliberation_planning_aligned`, `voice_execution_aligned`, `nova_lobe_voice_aligned`; `make alt15-1-gate`
- **Alt-15.2** — `NOVA_LOBE_V1_PROOF` + `COHERENCE_PROJECTION_ORGAN_V1_PROOF` + `SPEAKING_RUNTIME_ORGAN_V1_PROOF`; `make alt15-2-gate`
- **Governed promotion** — `tools/governance/alt15_promote_governed.py`; `make alt15-governed-gate`

### Changed

- Genome registry: **75 governed** subsystem genomes (66 prior + 9 Alt-15)
- `operator_cognition_coherence_fabric` schema ref → v1.10

### Verification (v1.11.0)

```bash
make alt15-gate alt15-1-gate alt15-2-gate alt15-governed-gate
python -m pytest tests/test_reasoning_executive_organ.py tests/test_attention_organ.py tests/test_coherence_projection_organ.py tests/test_deliberation_organ.py tests/test_planning_organ.py tests/test_cortex_arcs_organ.py tests/test_cognitive_execution_organ.py tests/test_speaking_runtime_organ.py tests/test_nova_face_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.11.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.11.0

## [1.10.0] - 2026-06-02 — Alt-14 Route Choice & Perception Fabric

**Alt-14** — nine read-only organs at governed; coherence fabric v1.9 with perception, spatial/symbolic, and route-choice posture planes.

### Added

- **Alt-14.0** — `document_vision_organ`, `ui_vision_organ`, `perception_gateway_organ`, `spatial_reasoning_organ`, `mystic_engine_organ`, `perception_lane_organ`, `route_choice_organ`, `specialist_route_organ`, `provider_route_organ`; status APIs; `make alt14-gate`; `tools/governance/alt14_promote_mvp.py`
- **Alt-14.1** — coherence snapshot v1.9 + `perception_aligned`, `spatial_symbolic_aligned`, `route_choice_aligned` in Tier 5; `make alt14-1-gate`
- **Alt-14.2** — `PERCEPTION_GATEWAY_V1_PROOF` + `ROUTE_CHOICE_V1_PROOF` + `SPATIAL_SYMBOLIC_V1_PROOF`; `make alt14-2-gate`
- **Governed promotion** — `tools/governance/alt14_promote_governed.py`; `make alt14-governed-gate`

### Changed

- Genome registry: **66 governed** subsystem genomes (57 prior + 9 Alt-14)
- `operator_cognition_coherence_fabric` schema ref → v1.9

### Verification (v1.10.0)

```bash
make alt14-gate alt14-1-gate alt14-2-gate alt14-governed-gate
python -m pytest tests/test_document_vision_organ.py tests/test_ui_vision_organ.py tests/test_perception_gateway_organ.py tests/test_spatial_reasoning_organ.py tests/test_mystic_engine_organ.py tests/test_perception_lane_organ.py tests/test_route_choice_organ.py tests/test_specialist_route_organ.py tests/test_provider_route_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.10.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.10.0

## [1.9.0] - 2026-06-02 — Alt-13 Creative Chain & Constitutional Closure Fabric

**Alt-13** — nine read-only organs at governed; coherence fabric v1.8 with constitutional creative, story chain, and module governance posture planes.

### Added

- **Alt-13.0** — `ul_lineage_console_organ`, `module_governance_organ`, `recipe_module_organ`, `imagine_generator_organ`, `story_forge_lane_organ`, `beatbox_lane_organ`, `speakers_lane_organ`, `human_voice_extraction_organ`, `narrative_trust_pack_organ`; status APIs; `make alt13-gate`; `tools/governance/alt13_promote_mvp.py`
- **Alt-13.1** — coherence snapshot v1.8 + `constitutional_creative_aligned`, `story_chain_aligned`, `module_governance_aligned` in Tier 5; `make alt13-1-gate`
- **Alt-13.2** — `STORY_CHAIN_V1_PROOF` + `CONSTITUTIONAL_CREATIVE_V1_PROOF` + `MODULE_GOVERNANCE_ORGAN_V1_PROOF`; `make alt13-2-gate`
- **Governed promotion** — `tools/governance/alt13_promote_governed.py`; `make alt13-governed-gate`

### Changed

- Genome registry: **57 governed** subsystem genomes (48 prior + 9 Alt-13)
- `operator_cognition_coherence_fabric` schema ref → v1.8

### Verification (v1.9.0)

```bash
make alt13-gate alt13-1-gate alt13-2-gate alt13-governed-gate
python -m pytest tests/test_ul_lineage_console_organ.py tests/test_module_governance_organ.py tests/test_recipe_module_organ.py tests/test_imagine_generator_organ.py tests/test_story_forge_lane_organ.py tests/test_beatbox_lane_organ.py tests/test_speakers_lane_organ.py tests/test_human_voice_extraction_organ.py tests/test_narrative_trust_pack_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.9.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.9.0

## [1.8.0] - 2026-06-02 — Alt-12 OTEM, Predictive Lane & Execution Depth Fabric

**Alt-12** — nine read-only organs at governed; coherence fabric v1.7 with OTEM lane, predictive lane, and execution-depth posture planes.

### Added

- **Alt-12.0** — `otem_bounded_organ`, `direct_challenge_organ`, `orchestration_spine_organ`, `operator_health_sentinel_organ`, `governed_realtime_lane_organ`, `v8_runtime_organ`, `patch_apply_organ`, `patch_execution_preview_organ`, `run_ledger_organ`; status APIs; `make alt12-gate`; `tools/governance/alt12_promote_mvp.py`
- **Alt-12.1** — coherence snapshot v1.7 + `otem_lane_aligned`, `predictive_lane_aligned`, `execution_depth_aligned` in Tier 5; `make alt12-1-gate`
- **Alt-12.2** — `OTEM_BOUNDED_V1_PROOF` + `PREDICTIVE_LANE_V1_PROOF` + `EXECUTION_DEPTH_V1_PROOF`; `make alt12-2-gate`
- **Governed promotion** — `tools/governance/alt12_promote_governed.py`; `make alt12-governed-gate`

### Changed

- Genome registry: **48 governed** subsystem genomes (39 prior + 9 Alt-12)
- `operator_cognition_coherence_fabric` schema ref → v1.7

### Verification (v1.8.0)

```bash
make alt12-gate alt12-1-gate alt12-2-gate alt12-governed-gate
python -m pytest tests/test_otem_bounded_organ.py tests/test_direct_challenge_organ.py tests/test_orchestration_spine_organ.py tests/test_operator_health_sentinel_organ.py tests/test_governed_realtime_lane_organ.py tests/test_v8_runtime_organ.py tests/test_patch_apply_organ.py tests/test_patch_execution_preview_organ.py tests/test_run_ledger_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.8.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.8.0

## [1.7.0] - 2026-06-02 — Alt-11 Authority Trace, Boundary & Coding Fabric

**Alt-11** — nine read-only organs at governed; coherence fabric v1.6 with authority trace, mission boundary, and coding posture planes.

### Added

- **Alt-11.0** — `cognitive_bridge_organ`, `governed_event_chain_organ`, `tracing_spine_organ`, `mission_board_organ`, `aris_boundary_organ`, `capability_module_organ`, `patchforge_organ`, `change_scope_organ`, `patch_verification_organ`; status APIs; `make alt11-gate`; `tools/governance/alt11_promote_mvp.py`
- **Alt-11.1** — coherence snapshot v1.6 + `authority_trace_aligned`, `mission_boundary_aligned`, `coding_stack_aligned` in Tier 5; `make alt11-1-gate`
- **Alt-11.2** — `TRACING_SPINE_V1_PROOF` + `CODING_ORGANS_V1_PROOF` + `MEMORY_PATH_CLOSURE_V1_PROOF`; `make alt11-2-gate`
- **Governed promotion** — `tools/governance/alt11_promote_governed.py`; `make alt11-governed-gate`

### Changed

- Genome registry: **39 governed** subsystem genomes (30 prior + 9 Alt-11)
- `operator_cognition_coherence_fabric` schema ref → v1.6

### Verification (v1.7.0)

```bash
make alt11-gate alt11-1-gate alt11-2-gate alt11-governed-gate
python -m pytest tests/test_cognitive_bridge_organ.py tests/test_governed_event_chain_organ.py tests/test_tracing_spine_organ.py tests/test_mission_board_organ.py tests/test_aris_boundary_organ.py tests/test_capability_module_organ.py tests/test_patchforge_organ.py tests/test_change_scope_organ.py tests/test_patch_verification_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.7.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.7.0

## [1.6.0] - 2026-06-02 — Alt-10 Memory, Forensics & Immune Observe Fabric

**Alt-10** — nine read-only organs at governed; coherence fabric v1.5 with memory, forensics, and immune observe posture planes.

### Added

- **Alt-10.0** — `verification_gate_organ`, `memory_path_governance_organ`, `knowledge_authority_organ`, `scorpion_bridge_organ`, `mechanic_handoff_organ`, `forensic_triangulation_organ`, `immune_observe_organ`, `policy_gate_organ`, `predictor_immune_bridge_organ`; status APIs; `make alt10-gate`; `tools/governance/alt10_promote_mvp.py`
- **Alt-10.1** — coherence snapshot v1.5 + `memory_paths_aligned`, `forensics_handoff_aligned`, `immune_observe_aligned` in Tier 5; `make alt10-1-gate`
- **Alt-10.2** — `IMMUNE_OBSERVE_V1_PROOF` + `MEMORY_PATH_GOVERNANCE_V1_PROOF`; `make alt10-2-gate`
- **Governed promotion** — `tools/governance/alt10_promote_governed.py`; `make alt10-governed-gate`

### Changed

- Genome registry: **30 governed** subsystem genomes (21 prior + 9 Alt-10)
- `operator_cognition_coherence_fabric` schema ref → v1.5

### Verification (v1.6.0)

```bash
make alt10-gate alt10-1-gate alt10-2-gate alt10-governed-gate
python -m pytest tests/test_verification_gate_organ.py tests/test_memory_path_governance_organ.py tests/test_knowledge_authority_organ.py tests/test_scorpion_bridge_organ.py tests/test_mechanic_handoff_organ.py tests/test_forensic_triangulation_organ.py tests/test_immune_observe_organ.py tests/test_policy_gate_organ.py tests/test_predictor_immune_bridge_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.6.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.6.0

## [1.5.0] - 2026-06-02 — Alt-9 Infrastructure Fabric

**Alt-9** — three infrastructure organs at governed; coherence fabric v1.4 `infrastructure_posture[]`; immune substrate closure.

### Added

- **Alt-9.0** — `phase_gate_organ`, `realtime_event_cause_predictor_organ`, `invariant_engine_organ`; status APIs; `make alt9-gate`; `tools/governance/alt9_promote_mvp.py`
- **Alt-9.1** — coherence snapshot v1.4 + `infrastructure_substrate_aligned` in Tier 5; `make alt9-1-gate`
- **Alt-9.2** — `IMMUNE_SUBSTRATE_V1_PROOF` + Nova doc substrate language; `make alt9-2-gate`
- **Governed promotion** — `tools/governance/alt9_promote_governed.py`; `make alt9-governed-gate`
- **Nova hook** — `compare_nova_runtime_invariants()` on companion turns

### Changed

- Genome registry: **21 governed** subsystem genomes (18 prior + 3 Alt-9)
- `operator_cognition_coherence_fabric` schema ref → v1.4

### Verification (v1.5.0)

```bash
make alt9-gate alt9-1-gate alt9-2-gate alt9-governed-gate
python -m pytest tests/test_phase_gate_organ.py tests/test_realtime_event_cause_predictor_organ.py tests/test_invariant_engine_organ.py tests/test_operator_cognition_coherence_fabric.py -q
```

[1.5.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.5.0

## [1.4.0] - 2026-06-02 — Alt-8 Cognitive Continuity & Witness

**Alt-8** — three mind-plane organs at governed; coherence fabric v1.3 `mind_posture[]`; MP-SE-001 safety envelope MP-X path.

### Added

- **Alt-8.0** — `continuity_witness_organ`, `narrative_continuity_organ`, `intent_agency_organ`; status APIs; `make alt8-gate`; `tools/governance/alt8_promote_mvp.py`
- **Alt-8.1** — coherence snapshot v1.3 + `mind_planes_aligned` in Tier 5; `make alt8-1-gate`
- **Alt-8.2** — `MP-SE-001` + `make safety-envelope-mutation-gate`; `make alt8-2-gate`
- **Governed promotion** — `tools/governance/alt8_promote_governed.py`; `make alt8-governed-gate`

### Changed

- Genome registry: **18 governed** subsystem genomes (15 prior + 3 Alt-8)
- `operator_cognition_coherence_fabric` schema ref → v1.3

### Verification (v1.4.0)

```bash
make alt8-gate alt8-1-gate alt8-2-gate alt8-governed-gate
python -m pytest tests/test_continuity_witness_organ.py tests/test_narrative_continuity_organ.py tests/test_intent_agency_organ.py tests/test_operator_cognition_coherence_fabric.py tests/test_safety_envelope_organ_mutation_MP_SE_001.py -q
```

[1.4.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.4.0

## [1.3.3] - 2026-06-02 — Alt-7.2 Enforcement Closure

**Alt-7.2** — hard-block Jarvis chat when `coherence_protocol` is BLOCK; coherence snapshot v1.2 with live pipeline join; witness/Tier 5 observability; MP-OPO-001 profile MP-X path.

### Added

- **Cognitive hard block** — `assert_coherence_allows_turn()` + 403 chat/stream responses (`AAIS_COHERENCE_HARD_BLOCK`, default on)
- **Snapshot v1.2** — `coherence_pipeline_allowed`, `safety_envelope_halt`, optional `last_coherence_*` from live pipeline
- **Status API** — `GET /api/jarvis/coherence-fabric/status?session_id=` joins last governed pipeline
- **Pipeline envelope** — `coherence_response` / `coherence_reason` in `signal_feed`
- **MP-OPO-001** — `operator_profile_organ` profile invariant MP-X; `make operator-profile-mutation-gate`
- **Umbrella gate** — `make alt7-2-gate`

### Changed

- Continuity witness records `coherence_boundary` and `coherence_protocol` surface
- Tier 5 health includes `coherence_pipeline_allowed` and `safety_envelope_halt`
- Genome coherence fabric schema ref → v1.2

### Verification (v1.3.3)

```bash
make alt7-2-gate
python -m pytest tests/test_coherence_fabric_chat_block.py \
  tests/test_coherence_fabric_pipeline.py tests/test_operator_profile_organ_mutation_MP_OPO_001.py -q
```

[1.3.3]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.3.3

## [1.3.2] - 2026-06-02 — Alt-7.1 Coherence Evolution

**Alt-7.1** — coherence fabric MP-X path (MP-OCCF-001), snapshot v1.1 with runtime posture planes, governance projection in Jarvis modular chat, and pipeline `coherence_protocol` guard.

### Added

- **Alt-7.1 MP-X** — `MP-OCCF-001` for `operator_cognition_coherence_fabric`; `make coherence-fabric-mutation-gate`; post-apply `alt7-governed-gate`
- **Snapshot v1.1** — `runtime_posture[]` joins `reflection_runtime_organ` and `memory_runtime_organ`
- **Governance projection** — `OperatorGovernanceCoherenceModule` (`AAIS_GOVERNANCE_COHERENCE_PROJECTION`, default on)
- **Pipeline guard** — `evaluate_pipeline_coherence()` + `coherence_protocol` on governed direct pipeline trace
- **Umbrella gate** — `make alt7-1-gate`

### Changed

- `MutationEngine` runs `alt7-governed-gate` on coherence MP-X; fabric `lane_dna` mutations also re-validate alt7
- Genome `operator_cognition_coherence_fabric` schema ref → v1.1

### Verification (v1.3.2)

```bash
make alt7-1-gate
python -m pytest tests/test_operator_cognition_coherence_fabric.py \
  tests/test_operator_cognition_coherence_fabric_mutation_MP_OCCF_001.py \
  tests/test_coherence_fabric_bridge.py tests/test_coherence_fabric_pipeline.py \
  tests/test_governance_coherence_projection.py -q
```

[1.3.2]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.3.2

## [1.3.1] - 2026-06-02 — Close Loops

**Close Loops** — live MP-ALO-001 lane DNA + MP-NTP-001 invariant mutations; Triangulation and Narrative Trust Pack Jarvis bridge/API routes; retirement lineage `migration_proof` on Alt-5/6/7 dependents.

### Added

- **MP-ALO-001 live** — `audit_lane_mutation` on operator lane; post-apply wake + alt6 fabric re-validation
- **MP-NTP-001 bundle** — dedicated mutation gate, proof doc, post-apply `narrative-gate` hook; live invariant append
- **Forensic Triangulation Jarvis route** — `forensic_triangulation` / `correlate`; `POST /api/jarvis/triangulation/correlate`
- **NTP Jarvis routes** — `narrative_trust_pack` pack/verify/signoff; `POST /api/jarvis/narrative/{pack,verify,signoff}`

### Changed

- Governance gates include bridge tests for triangulation and narrative
- Dependent genomes (`adaptive_lane_organ`, `operator_cognition_coherence_fabric`, `reflection_runtime_organ`) carry `retirement.migration_proof` for `operator_profile_organ` lineage gate
- Mutation apply/rollback tests skip when live genome already promoted

### Verification (v1.3.1)

```bash
make adaptive-lane-mutation-gate narrative-trust-pack-mutation-gate
make triangulation-gate narrative-gate genome-gate
python -m pytest tests/test_capability_bridge_alt3.py tests/test_governance_organs_alt4.py \
  tests/test_adaptive_lane_organ_mutation_MP_ALO_001.py tests/test_narrative_trust_pack_mutation_MP_NTP_001.py -q
```

[1.3.1]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.3.1

## [1.3.0] - 2026-06-02 — Infinity 1 · Alt-7

**Infinity 1 · Alt-7** — fifteenth governed genome (`operator_cognition_coherence_fabric`); cross-plane coherence snapshot joins profile, lanes, and envelopes; capability bridge execute-path enforcement when fabric is misaligned or policy caps run under non-strict posture. Includes Alt-6.1 lane mutation golden path (MP-ALO-001).

### Added

- **Alt-7 Summon Wave** — `operator_cognition_coherence_fabric` at `governed`; `GET /api/jarvis/coherence-fabric/status`; `src/operator_cognition_coherence_fabric.py`
- **Cross-plane enforcement** — `evaluate_bridge_coherence()` on capability bridge `_execute_spec`; blocks on fabric misalignment, safety halt, and non-strict bridge mode for policy capabilities
- **Governance gates** — `make alt7-gate`, `make alt7-governed-gate`; `tools/governance/check_alt7_governed_eligibility.py`
- **Promotion** — `tools/governance/alt7_promote_mvp.py`, `tools/governance/alt7_promote_governed.py`
- **Alt-6.1 lane mutation** — MP-ALO-001 golden path; `MutationEngine` lane_dna apply with post-apply wake; `make adaptive-lane-mutation-gate`

### Changed

- Fifteen registered subsystem genomes; lineage `children` on six Alt-7 parent genomes
- [AAIS_SSP_PROTOCOL.md](docs/contracts/AAIS_SSP_PROTOCOL.md) — Alt-7 governed promotion section
- [AAIS_ADAPTIVE_GOVERNANCE.md](docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md) — Alt-7 governed checklist + bridge enforcement
- Tier 5 health includes `coherence_fabric_aligned`

### Verification (v1.3.0)

```bash
make alt7-governed-gate
make genome-gate alt6-governed-gate
python -m pytest tests/test_coherence_fabric_bridge.py tests/test_alt7_governed_eligibility.py \
  tests/test_operator_cognition_coherence_fabric.py tests/test_adaptive_lane_organ_mutation_MP_ALO_001.py -q
python tools/governance/alt7_promote_governed.py  # idempotent when already governed
```

[1.3.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.3.0

## [1.2.0] - 2026-06-02 — Infinity 1 · Alt-6

**Infinity 1 · Alt-6** — fourteenth governed genome (`adaptive_lane_organ`); Tier 5 operator-weighted lanes wake into live runtime with fabric-minimum eligibility and governed promotion tooling.

### Added

- **Alt-6 Summon Wave** — `adaptive_lane_organ` at `governed`; `GET /api/jarvis/adaptive-lanes/status`; `src/adaptive_lane_organ.py`
- **Adaptive lane wake** — boot `Tier5Governance.wake_lanes()`; persistence to `.runtime/governance/adaptive_lanes.json`
- **Fabric minimum** — `operator_lanes` DNA on `adaptive_lane_organ`, `operator_profile_organ`, `capability_service_bridge`, `recipe_module`, `governed_direct_pipeline`
- **Governance gates** — `make alt6-gate`, `make alt6-governed-gate`; `tools/governance/check_alt6_governed_eligibility.py`
- **Promotion** — `tools/governance/alt6_promote_mvp.py`, `tools/governance/alt6_promote_governed.py`
- **Bridge enforcement** — capability bridge lane resolution + policy-cap authority mismatch block

### Changed

- Fourteen registered subsystem genomes; [AAIS_SUBSYSTEM_SPEC.md](docs/runtime/AAIS_SUBSYSTEM_SPEC.md) §8 extended with Adaptive Lane Organ
- [AAIS_SSP_PROTOCOL.md](docs/contracts/AAIS_SSP_PROTOCOL.md) — Alt-6 governed promotion section
- [AAIS_ADAPTIVE_GOVERNANCE.md](docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md) — Governed Lane Fabric checklist
- `PromotionEngine.evaluate(..., run_gates=False)` for tier5 health audit (prevents recursive gate freeze)
- Tier 5 health report includes `adaptive_lanes_awakened` and `adaptive_lane_count`

### Verification (v1.2.0)

```bash
make alt6-governed-gate
make genome-gate alt4-gate tier5-gate
python -m pytest tests/test_adaptive_lane_organ.py tests/test_alt6_governed_eligibility.py \
  tests/test_adaptive_lane_bridge.py tests/test_adaptive_governance.py -q
python tools/governance/alt6_promote_governed.py  # idempotent when already governed
```

[1.2.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.2.0

## [1.1.0] - 2026-06-02 — Infinity 1 (complete)

**Infinity 1 (complete)** — thirteen governed subsystem genomes, Alt-5 waves 1–2 (four organs at `governed`), barebones summon wave (bridge, memory board, governed pipeline), and reproducible promotion scripts.

### Added

- **Alt-5 Summon Wave 2** — `reflection_runtime_organ`, `memory_runtime_organ` at `governed`; `GET /api/jarvis/reflection-runtime/status`, `GET /api/jarvis/memory-runtime/status`; `tools/governance/alt5_promote_wave2_mvp.py`
- **Alt-5 governed promotion** — all four Alt-5 organs (`safety_envelope_organ`, `operator_profile_organ`, reflection, memory) at `governed`; `tools/governance/alt5_promote_governed.py`
- **Barebones summon wave** — `capability_service_bridge`, `jarvis_memory_board`, `governed_direct_pipeline` at `governed`; status APIs and `make barebones-gate`; `tools/governance/barebones_promote_governed.py`
- **Governance gates** — `reflection-runtime-gate`, `memory-runtime-gate`, capability-bridge, memory-board, governed-pipeline checks

### Changed

- Thirteen registered subsystem genomes (all at `governed`); [AAIS_SUBSYSTEM_SPEC.md](docs/runtime/AAIS_SUBSYSTEM_SPEC.md) §8 constitutional layer extended
- [AAIS_SSP_PROTOCOL.md](docs/contracts/AAIS_SSP_PROTOCOL.md) — Alt-5 wave 2 + governed promotion path
- `make alt5-gate` includes wave 2 organ gates

### Verification (v1.1.0)

```bash
make genome-gate alt4-gate alt5-gate barebones-gate tier5-gate
python -m pytest tests/test_safety_envelope_organ.py tests/test_operator_profile_organ.py \
  tests/test_reflection_runtime_organ.py tests/test_memory_runtime_organ.py \
  tests/test_governance_organs_alt4.py tests/test_adaptive_governance.py -q
python tools/governance/alt5_promote_governed.py  # idempotent when already governed
```

[1.1.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.1.0

## [1.0.0] - 2026-06-02 — Infinity 1

**Infinity 1** — self-governing runtime: Alt-4 lifecycle organs, constitutional layer (six governed genomes), Alt-5 summon wave (two new organs), Governance Tier 5 adaptive layer.

### Added

- **Alt-4 Runtime Organs** — `src/governance_organs/` (Genome, Promotion, Mutation, Retirement engines); boot hooks in `src/api.py` and `app/main.py`; capability-bridge DNA enforcement; `make alt4-gate`, `promotion-scan`, `promotion-apply`; MP-NTP-001 golden mutation path; [AAIS_ALT4_RUNTIME_OPERATOR_GUIDE.md](docs/contracts/AAIS_ALT4_RUNTIME_OPERATOR_GUIDE.md)
- **Governed Subsystem Expansion** — all six original genomes at `governed` (lineage console, triangulation, NTP, recipe, imagine, human voice)
- **Alt-5 Summon Wave** — `safety_envelope_organ`, `operator_profile_organ` at MVP; `GET /api/jarvis/safety-envelope/status`, `GET /api/jarvis/operator-profile`; `make alt5-gate`
- **Governance Tier 5** — [AAIS_ADAPTIVE_GOVERNANCE.md](docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md), `AdaptiveEngine`, `make tier5-gate`, contextual gates on capability bridge; `recipe_module` pilot

### Changed

- Eight registered subsystem genomes (six governed + two Alt-5 MVP); [AAIS_SUBSYSTEM_SPEC.md](docs/runtime/AAIS_SUBSYSTEM_SPEC.md) §8 constitutional layer
- [AAIS_SSP_PROTOCOL.md](docs/contracts/AAIS_SSP_PROTOCOL.md) — Alt-4 runtime organs + Alt-5 summon wave sections

### Verification (v1.0.0)

```bash
make genome-gate alt4-gate alt5-gate tier5-gate
python -m pytest tests/test_governance_organs_alt4.py tests/test_adaptive_governance.py tests/test_safety_envelope_organ.py tests/test_operator_profile_organ.py -q
```

[1.0.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.0.0

## [0.4.0] - 2026-06-02

Three Ideas MVP — CISIV Lineage Console, Forensic Triangulation Ledger, and Narrative Trust Pack promoted from concept to **partial live**.

### Added

- **CISIV Lineage Console** — `src/ul_lineage.py`, emitter hooks (chat, memory, capability, forge), `GET /api/jarvis/lineage/<mission_id>`, Operator CISIV Lineage panel, `tools.ul.smoke --lineage-graph`, `tools.ul.drift --lane lineage`
- **Forensic Triangulation** — `triangulation/` package, `python -m triangulation correlate`, fixture `tri-demo-001`, bridge map GOV-CI-03 ↔ fd_flow, `make triangulation-gate`
- **Narrative Trust Pack** — `src/capabilities/narrative_trust_pack.py`, `python -m tools.narrative pack|verify|signoff`, E2E + tamper tests, `make narrative-gate`
- **Proof packets** — `docs/proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md`, `docs/proof/forensics/TRIANGULATION_V1_PROOF.md`, `docs/proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md`
- **Docs** — active runtime/subsystem docs; `docs/_future/ideas_pending/` concept specs updated to implementation stage

### Changed

- `docs/runtime/AAIS_SUBSYSTEM_SPEC.md` — §8 Three Ideas MVP partial-live table
- `README.md` — v0.4.0 release section and verification commands

### Verification (v0.4.0)

```bash
make lineage-gate triangulation-gate narrative-gate
python -m pytest tests/test_ul_lineage.py tests/test_triangulation.py tests/test_narrative_trust_pack.py -q
python -m tools.ul.smoke --lineage-graph tools/ul/fixtures/lineage_multi_hop.json --no-pytest
```

[0.4.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v0.4.0

## [0.3.0] - 2026-06-02

Audit Alt-3 — Recipe Module, Imagine Generator, and Human Voice Extraction promoted from concept to **partial live**, with capability bridge catalog, UL lineage hooks, and env-gated Grok imagine rendering.

### Added

- **Recipe Module** — governed recipe packs, `mission_board.create_from_recipe`, `POST /api/jarvis/missions/from-recipe`, capability bridge `recipe_module` / `create_mission`, fixture `tools/recipe/fixtures/onboarding-v1.json`
- **Imagine Generator** — pattern emit, Story Forge admission handoff, `POST /api/jarvis/imagine/emit` and `/handoff`, capability bridge `imagine_generator` / `emit`, `handoff`, `grok_render`
- **Human Voice Extraction** — extract / signoff / Speakers constraints handoff (no raw notes persisted), human-voice API, capability bridge `human_voice_extraction` / `extract`, `signoff`, `handoff`
- **Alt-3 deferred wiring** — `src/alt3_lineage.py` subsystem-specific UL lineage; `src/imagine_grok.py` with env-only xAI keys (`STORY_FORGE_XAI_API_KEY`, `XAI_API_KEY`); `GET /api/jarvis/imagine/keys-status`, `POST /api/jarvis/imagine/grok-render` (428 `keys_required` when unset)
- **Governance** — SSP concept bundles for all three families; `make alt3-gate`, `recipe-module-gate`, `imagine-generator-gate`, `human-voice-extraction-gate`, `ssp-gate`, `genome-gate`; proof packets under `docs/proof/platform/`, `docs/proof/storyforge/`, `docs/proof/speakers/`
- **SSP Alt-4** — subsystem genome meta-schema, promotion/retirement/mutation protocols, genome registry (`governance/`)

### Changed

- `docs/runtime/AAIS_SUBSYSTEM_SPEC.md` — §8 partial-live entries for Recipe Module, Imagine Generator, Human Voice Extraction
- `docs/operations/FIRST_TIME_OPERATOR_GUIDE.md` — Grok API key paragraph for imagine render
- Capability bridge catalog extended in `src/capability_service_bridge.py`

### Security

- Grok/xAI API keys are read **only** from environment variables — no per-request key override, no persistence in artifacts (hashes only in `grok_render.json`)

### Verification (v0.3.0)

```bash
make alt3-gate
python -m pytest tests/test_recipe_module.py tests/test_imagine_generator.py tests/test_human_voice_extraction.py -q
python -m pytest tests/test_capability_bridge_alt3.py tests/test_alt3_lineage.py tests/test_imagine_grok.py -q
python tools/governance/check_ssp_completeness.py
```

[0.3.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v0.3.0

## [0.2.0] - 2026-06-02

Initial public release of Project Infinity / AAIS as an Apache 2.0 monorepo.

### Added

- Cross-platform launcher (`python -m aais start | prepare | doctor`)
- FastAPI workflow shell with packaged React operator UI (`app/`, `frontend/`)
- Jarvis cognition runtime with UL substrate, Project Infi law, and CISIV staging (`src/`)
- Provider registry: mock, laptop, local, OpenAI, Anthropic, OpenRouter routes
- Optional forge/evolve contractor lanes (`forge/`, `forge_eval/`, `evolve_engine/`)
- Platform Membrane multi-tenant ops ingress (`platform/`)
- Infinity Pilot Docker stack (`deploy/pilot/`)
- Wolf-CoG-OS ISO/rootfs forge scripts (`wolf-cog-os/`)
- UL drift/smoke tooling (`tools/ul/`)
- Governance CI gates (CoGOS CI, UGR trust bundle, documentation baseline, Forgekeeper, Scorpion, repo hygiene)
- First-Time Operator Guide and architecture README sections
- Apache 2.0 [LICENSE](LICENSE), [SECURITY.md](SECURITY.md), root [.env.example](.env.example)

### Changed

- README restructured with architecture diagram, tiered entry paths, and expanded repo layout
- Repo hygiene enforced via `check-repo-hygiene.py` and `REPO_HYGIENE_MANIFEST.json`

### Fixed

- Detachment guard exposed through governed read/clear API routes with regression coverage
- Ingress route identity preserved across message, stream, and compat lanes

### Security

- Removed tracked Wolf-CoG-OS operator backup bundles containing development signing keys
- Added `.gitignore` rule for `wolf-cog-os/payload/opt/cogos/memory/backups/*`
- Documented production hardening checklist in SECURITY.md

### Known limits

- Infinity Pilot is early-adopter, not GA — see [INFINITY_PILOT_BASELINE_CHECKLIST.md](docs/baseline/INFINITY_PILOT_BASELINE_CHECKLIST.md)
- Scorpion operational runbook is a skeleton
- Platform OIDC and multi-tenant K8s hardening partially open
- CoGOS ISO promotion requires GitHub Actions minisign secrets (not in repo)

### Verification (v0.2.0)

```bash
python -m pytest tests/test_cisiv.py tests/test_chat_turn_governance.py -q
python -m tools.ul.smoke
curl -fsS http://127.0.0.1:8000/health
make stack-pilot-gate   # Tier 2 Infinity Pilot only
```

[0.2.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v0.2.0
