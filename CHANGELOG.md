# Changelog

All notable changes to the **AAIS Python runtime and operator surfaces** are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

CoGOS ISO releases are tracked separately — see [docs/releases/README.md](docs/releases/README.md).

## [Unreleased]

### Added

- (none yet)

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
