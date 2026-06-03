# AAIS Subsystem Summoner Pattern (SSP)

Status: **active contract**

CISIV stage: **structure**

## Purpose

SSP is a deterministic pattern that takes raw idea seeds and transforms them into
fully governed subsystem families before any runtime code is written. Cursor runs
SSP on demand via the project skill at `.cursor/skills/subsystem-summoner/`.

This protocol prevents **ghost subsystems** — features referenced in conversation
or docs without schema, concept spec, proof posture, MVP plan, or doc tree wiring.

## Summon Command

```text
Cursor, summon N subsystem families: <seed 1>, <seed 2>, …
```

Alternate triggers: "run SSP on …", "admit concept …"

## Input

N idea seeds — short descriptions such as:

- "Operator lineage graph"
- "Triangulation ledger"
- "Narrative trust pack"

Optional: dependency hints, target subsystem README, proof subdirectory.

## Output (Per Idea)

| Deliverable | Location |
|-------------|----------|
| Concept spec (CISIV concept stage) | `docs/_future/ideas_pending/<NAME>.md` |
| Schema | `schemas/<name>.v1.json` + `docs/_future/ideas_pending/schemas/` copy |
| MVP plan | `docs/_future/ideas_pending/<NAME>_MVP_PLAN.md` |
| Doc tree wiring | Indexes, subsystem READMEs, `AAIS_SUBSYSTEM_SPEC.md` |
| Audit entry | `docs/audit/LOGBOOK.md` |
| Proof posture | §8 in concept spec; claims default `none_yet` |

## Seven-Step Pipeline (SSP + Alt-4)

| Step | Action |
|------|--------|
| 1 | Generate concept spec |
| 2 | Generate schema (canonical + concept-origin copy) |
| 3 | Wire doc tree |
| 4 | Add audit entry (CISIV stage `concept`) |
| 5 | Generate MVP plan |
| 6 | (Optional) Scaffold code stubs — no full logic unless asked |
| 7 | Generate subsystem genome at `governance/subsystem_genomes/<gene>.genome.v1.json` |

Full execution checklist: [.cursor/skills/subsystem-summoner/SKILL.md](../../.cursor/skills/subsystem-summoner/SKILL.md)

## Governance Rule

No subsystem becomes real until it has **all** of:

1. Schema
2. Concept spec
3. Proof posture table
4. MVP plan
5. Doc tree wiring
6. Subsystem genome (Alt-4)

Enforced by `make ssp-gate` and `make genome-gate` (every admitted family has a genome record).

## SSP Alt-4 (Governance-of-Governance)

Alt-4 adds lifecycle contracts, mutation/retirement paths, and the **Subsystem
Genome** meta-schema:

| Artifact | Path |
|----------|------|
| Promotion protocol | [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md) |
| Retirement protocol | [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md) |
| Mutation path | [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md) |
| Subsystem genome | [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md) |
| Meta-schema | [schemas/subsystem_genome.v1.json](../../schemas/subsystem_genome.v1.json) |
| Genome registry | [governance/subsystem_genomes/](../../governance/subsystem_genomes/) |

Gates: `make ssp-gate` + `make genome-gate`

## Alt-4 Runtime Organs

Governance-of-governance protocols are executable at runtime via
`src/governance_organs/`:

| Organ | Module | Role |
|-------|--------|------|
| Genome Engine | `genome_engine.py` | Validates DNA on boot, `make genome-gate`, and capability-bridge calls |
| Promotion Engine | `promotion_engine.py` | Full-auto `concept → prototype → mvp → governed` when gates pass |
| Mutation Engine | `mutation_engine.py` | MP-X apply/rollback with `schemas/deltas/` |
| Retirement Engine | `retirement_engine.py` | 10-step retirement state machine with lineage preservation |

Facade: `Alt4Runtime` in `src/governance_organs/__init__.py`.

Operator guide: [AAIS_ALT4_RUNTIME_OPERATOR_GUIDE.md](./AAIS_ALT4_RUNTIME_OPERATOR_GUIDE.md)

Makefile targets:

```bash
make alt4-gate          # genome-gate + promotion eligibility scan
make alt4-gate-strict   # same, but fail when promotions are pending
make promotion-scan     # dry-run next-stage evaluation for all genes
make promotion-apply    # full-auto apply when eligible
make retirement-scan    # dry-run retirement step report for all genes
make retirement-apply   # apply retirement advance (GENE= STEP= required)
```

Boot hook: Flask (`src/api.py`) and workflow shell (`app/main.py`) call
`Alt4Runtime.boot_validate()` unless `AAIS_GENOME_BOOT=warn`.

Step 7 summon completes when the genome exists **and** runtime organs can enforce
lifecycle transitions without manual registry surgery.

## Alt-5 Summon Wave

Batch-admit new subsystem families via the [subsystem-summoner skill](../../.cursor/skills/subsystem-summoner/SKILL.md).

| Convention | Value |
|------------|-------|
| Batch id | `alt5-summon-wave-YYYY-MM` in LOGBOOK + `activation.batch_id` |
| Initial stage | `concept` — empty `runtime.surface` |
| MVP promotion | `tools/governance/alt5_promote_mvp.py` or Promotion Engine twice (`concept→prototype→mvp`) |
| Gates | `make alt5-gate` — Alt-5 organ gates + `genome-gate` |

Wave 1 (2026-06): `safety_envelope_organ`, `operator_profile_organ`.

Wave 2 (2026-06): `reflection_runtime_organ`, `memory_runtime_organ` (Nova cortex lobes;
batch `alt5-summon-wave-2-2026-06`; promotion via `tools/governance/alt5_promote_wave2_mvp.py`).

All four Alt-5 organs may be promoted `mvp` → `governed` via
`tools/governance/alt5_promote_governed.py` or per-gene `promotion_engine --apply`.

## Alt-6 Summon Wave — Adaptive Lanes Wake Up

Batch-admit Tier 5 **operator-weighted lanes** into live runtime via the Adaptive Lane Organ.

| Convention | Value |
|------------|-------|
| Batch id | `alt6-summon-wave-YYYY-MM` in LOGBOOK + `activation.batch_id` |
| Initial stage | `concept` — empty `runtime.surface` |
| MVP promotion | `tools/governance/alt6_promote_mvp.py` or Promotion Engine twice |
| Gates | `make alt6-gate` — adaptive-lane-gate + tier5-gate + genome-gate |

Wave 1 (2026-06): `adaptive_lane_organ` — wakes genome `operator_lanes` DNA into
`.runtime/governance/adaptive_lanes.json`, boot hook via `Tier5Governance.wake_lanes()`,
and capability bridge lane resolution.

## Alt-6 Governed Promotion

Promote the adaptive lane fabric from **MVP → governed** when the fabric minimum
is proven and gates pass.

| Convention | Value |
|------------|-------|
| Eligibility | `make alt6-governed-gate` |
| Promotion | `tools/governance/alt6_promote_governed.py` or `promotion_engine --apply` |
| Proof bundle | `docs/proof/platform/ADAPTIVE_LANE_GOVERNED_PROOF.md` |

**Fabric minimum** — these genes MUST carry valid `governance.operator_lanes`:

- `adaptive_lane_organ`, `operator_profile_organ`, `capability_service_bridge`,
  `recipe_module`, `governed_direct_pipeline`

**Awakened registry** (`.runtime/governance/adaptive_lanes.json`):

- `awakened == true`
- `genes_with_lanes` includes all five fabric genes
- `authority_lane == "operator"`
- merged `operator` lane present

**Runtime enforcement (proven):**

- Boot wake via `Tier5Governance.wake_lanes()`
- Capability bridge lane resolution + policy-cap block on authority mismatch
- Tier 5 health reports `adaptive_lanes_awakened` (health audit uses `run_gates=False`)

**Genome at governed apply:**

- `adaptive_lane_organ` invariants maturity-tagged (`constitutional` / `stable`)
- `identity.version` → `1.0.0-governed`; `proof.posture` → `governed`

Operator checklist:

```bash
make alt6-governed-gate
python tools/governance/alt6_promote_governed.py
make alt4-gate
make tier5-gate
```

See [AAIS_ADAPTIVE_GOVERNANCE.md](./AAIS_ADAPTIVE_GOVERNANCE.md) § Governed Lane Fabric.

## Alt-6.1 Lane Mutation (MP-X)

Evolve fabric `operator_lanes` DNA under the constitutional invariant
*Wake is read-only — no lane mutation without MP-X*.

| Convention | Value |
|------------|-------|
| Contract | [AAIS_ADAPTIVE_GOVERNANCE.md](./AAIS_ADAPTIVE_GOVERNANCE.md) § Alt-6.1 |
| Golden proposal | `MP-ALO-001` for `adaptive_lane_organ` |
| Lane delta | `schemas/deltas/adaptive_lane_organ_MP-ALO-001.json` |
| Gate | `make adaptive-lane-mutation-gate` |
| Post-apply | `wake_adaptive_lanes()` + `make alt6-governed-gate` when fabric genes change |

## Alt-7 Summon Wave — Operator–Cognition Coherence Fabric

Cross-plane coherence snapshot joining profile, lanes, and envelope posture.

| Convention | Value |
|------------|-------|
| Batch id | `alt7-summon-wave-2026-06` in LOGBOOK |
| Initial stage | `concept` — genome + schema at admission |
| MVP promotion | `tools/governance/alt7_promote_mvp.py` or Promotion Engine twice |
| Gates | `make alt7-gate` — coherence-fabric-gate + alt6-governed-gate + genome-gate |
| Proof | `docs/proof/platform/OPERATOR_COGNITION_COHERENCE_FABRIC_V1_PROOF.md` |

Wave 1 (2026-06): `operator_cognition_coherence_fabric` — read-only
`build_coherence_fabric_status()` joins operator profile, awakened lanes, and envelope
governance modes; `GET /api/jarvis/coherence-fabric/status`.

Depends on: Alt-5 profile + envelope organs; Alt-6 governed lane fabric; Alt-6.1 MP-X path.

See [AAIS_ADAPTIVE_GOVERNANCE.md](./AAIS_ADAPTIVE_GOVERNANCE.md) § Alt-7.

## Alt-7 Governed Promotion

Promote coherence fabric from **MVP → governed** when cross-plane enforcement is proven.

| Convention | Value |
|------------|-------|
| Eligibility | `make alt7-governed-gate` |
| Promotion | `tools/governance/alt7_promote_governed.py` or `promotion_engine --apply` |
| Proof bundle | `docs/proof/platform/OPERATOR_COGNITION_COHERENCE_FABRIC_GOVERNED_PROOF.md` |
| Runtime enforcement | `evaluate_bridge_coherence()` in capability bridge `_execute_spec` |

Operator checklist:

```bash
make alt7-governed-gate
python tools/governance/alt7_promote_governed.py
make alt4-gate
make tier5-gate
```

## Alt-7.1 Coherence Fabric Evolution

| Convention | Value |
|------------|-------|
| Batch id | `alt7-1-summon-wave-2026-06` in LOGBOOK |
| Contract | [AAIS_ADAPTIVE_GOVERNANCE.md](./AAIS_ADAPTIVE_GOVERNANCE.md) § Alt-7.1 |
| Golden proposal | `MP-OCCF-001` for `operator_cognition_coherence_fabric` |
| Gate | `make coherence-fabric-mutation-gate`, `make alt7-1-gate` |
| Post-apply | `alt7-governed-gate` + `build_coherence_fabric_status()` aligned |
| Snapshot v1.1 | `schemas/operator_cognition_coherence_fabric.v1.1.json` + `runtime_posture[]` |
| Cognition bridge | `OperatorGovernanceCoherenceModule` in `jarvis_modular.py` |
| Pipeline guard | `evaluate_pipeline_coherence()` in `build_governed_turn_pipeline` |

Depends on: Alt-7 governed fabric; Alt-6.1 lane MP-X path.

## Alt-7.2 Coherence Enforcement Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt7-2-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.2` + live `pipeline_trace` |
| Hard block | `assert_coherence_allows_turn()` on Jarvis chat paths |
| Profile MP-X | `MP-OPO-001` + `make operator-profile-mutation-gate` |
| Gate | `make alt7-2-gate` |

## Alt-8 Summon Wave — Cognitive Continuity & Witness

Batch-admit Nova mind-plane organs as read-only governance shells.

| Convention | Value |
|------------|-------|
| Batch id | `alt8-summon-wave-2026-06` in LOGBOOK |
| Activation order | `continuity_witness_organ` → `narrative_continuity_organ` → `intent_agency_organ` |
| MVP promotion | `tools/governance/alt8_promote_mvp.py` |
| Gates | `make alt8-gate` |
| Governed promotion | `tools/governance/alt8_promote_governed.py` + `make alt8-governed-gate` |

Depends on: Alt-7.2 governed coherence fabric; Nova v3 narrative and intent proof bundles.

## Alt-8.1 Coherence Fabric Mind-Plane Join

| Convention | Value |
|------------|-------|
| Batch id | `alt8-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.3` + `mind_posture[]` |
| Gate | `make alt8-1-gate` |

## Alt-8.2 Safety Envelope MP-X

| Convention | Value |
|------------|-------|
| Batch id | `alt8-2-summon-wave-2026-06` in LOGBOOK |
| Golden proposal | `MP-SE-001` for `safety_envelope_organ` |
| Gate | `make alt8-2-gate` |

## Alt-9 Summon Wave — Admission, Prediction & Invariant Fabric

Batch-admit infrastructure organs as read-only governance shells over seeded runtime.

| Convention | Value |
|------------|-------|
| Batch id | `alt9-summon-wave-2026-06` in LOGBOOK |
| Activation order | `phase_gate_organ` → `realtime_event_cause_predictor_organ` → `invariant_engine_organ` |
| MVP promotion | `tools/governance/alt9_promote_mvp.py` |
| Gates | `make alt9-gate` |
| Governed promotion | `tools/governance/alt9_promote_governed.py` + `make alt9-governed-gate` |

Depends on: Alt-8 governed mind-plane organs; live governed direct pipeline predictor path; Nova anchor scaffold for invariant consumer attestation.

## Alt-9.1 Coherence Fabric Infrastructure Join

| Convention | Value |
|------------|-------|
| Batch id | `alt9-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.4` + `infrastructure_posture[]` |
| Gate | `make alt9-1-gate` |

## Alt-9.2 Immune Substrate Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt9-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/nova/IMMUNE_SUBSTRATE_V1_PROOF.md` |
| Gate | `make alt9-2-gate` |

## Alt-10 Summon Wave — Memory, Forensics & Immune Observe Fabric

Batch-admit nine read-only organs across memory/execution, forensics handoff, and bounded immune observe escalation.

| Convention | Value |
|------------|-------|
| Batch id | `alt10-summon-wave-2026-06` in LOGBOOK |
| Activation order | `verification_gate_organ` → `memory_path_governance_organ` → `knowledge_authority_organ` → `scorpion_bridge_organ` → `mechanic_handoff_organ` → `forensic_triangulation_organ` → `immune_observe_organ` → `policy_gate_organ` → `predictor_immune_bridge_organ` |
| MVP promotion | `tools/governance/alt10_promote_mvp.py` |
| Gates | `make alt10-gate` |
| Governed promotion | `tools/governance/alt10_promote_governed.py` + `make alt10-governed-gate` |

Depends on: Alt-9 governed infrastructure fabric; existing `forensic_triangulation` genome; immune substrate (Alt-9.2).

## Alt-10.1 Coherence Fabric Memory/Forensics/Immune Join

| Convention | Value |
|------------|-------|
| Batch id | `alt10-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.5` + `memory_governance_posture[]`, `forensics_posture[]`, `immune_observe_posture[]` |
| Gate | `make alt10-1-gate` |

## Alt-10.2 Immune Observe & Memory Path Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt10-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/nova/IMMUNE_OBSERVE_V1_PROOF.md`, `docs/proof/platform/MEMORY_PATH_GOVERNANCE_V1_PROOF.md` |
| Gate | `make alt10-2-gate` |

## Alt-11 Summon Wave — Authority Trace, Boundary & Coding Fabric

Batch-admit nine read-only organs across authority/trace spine, mission/boundary closure, and coding/patch verification.

| Convention | Value |
|------------|-------|
| Batch id | `alt11-summon-wave-2026-06` in LOGBOOK |
| Activation order | `cognitive_bridge_organ` → `governed_event_chain_organ` → `tracing_spine_organ` → `mission_board_organ` → `aris_boundary_organ` → `capability_module_organ` → `patchforge_organ` → `change_scope_organ` → `patch_verification_organ` |
| MVP promotion | `tools/governance/alt11_promote_mvp.py` |
| Gates | `make alt11-gate` |
| Governed promotion | `tools/governance/alt11_promote_governed.py` + `make alt11-governed-gate` |

Depends on: Alt-10 governed memory/forensics/immune fabric; AAIS_TRACING_PROTOCOL; live cognitive bridge and coding stack modules.

## Alt-11.1 Authority, Mission & Coding Coherence Join

| Convention | Value |
|------------|-------|
| Batch id | `alt11-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.6` + `authority_trace_posture[]`, `mission_boundary_posture[]`, `coding_posture[]` |
| Gate | `make alt11-1-gate` |

## Alt-11.2 Tracing & Coding Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt11-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/platform/TRACING_SPINE_V1_PROOF.md`, `docs/proof/platform/CODING_ORGANS_V1_PROOF.md`, `docs/proof/platform/MEMORY_PATH_CLOSURE_V1_PROOF.md` |
| Gate | `make alt11-2-gate` |

## Alt-12 Summon Wave — OTEM, Predictive Lane & Execution Depth Fabric

Batch-admit nine read-only organs across OTEM bounded reasoning, predictive realtime lanes, and execution-depth patch posture.

| Convention | Value |
|------------|-------|
| Batch id | `alt12-summon-wave-2026-06` in LOGBOOK |
| Activation order | `otem_bounded_organ` → `direct_challenge_organ` → `orchestration_spine_organ` → `operator_health_sentinel_organ` → `governed_realtime_lane_organ` → `v8_runtime_organ` → `patch_apply_organ` → `patch_execution_preview_organ` → `run_ledger_organ` |
| MVP promotion | `tools/governance/alt12_promote_mvp.py` |
| Gates | `make alt12-gate` |
| Governed promotion | `tools/governance/alt12_promote_governed.py` + `make alt12-governed-gate` |

Depends on: Alt-11 governed authority/coding fabric; live `otem_runtime.py`; `operator_health_sentinel.py`; Alt-9 predictor substrate.

## Alt-12.1 Coherence Fabric OTEM/Predictive/Execution Join

| Convention | Value |
|------------|-------|
| Batch id | `alt12-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.7` + `otem_lane_posture[]`, `predictive_lane_posture[]`, `execution_depth_posture[]` |
| Gate | `make alt12-1-gate` |

## Alt-12.2 OTEM & Predictive Lane Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt12-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/platform/OTEM_BOUNDED_V1_PROOF.md`, `docs/proof/platform/PREDICTIVE_LANE_V1_PROOF.md`, `docs/proof/platform/EXECUTION_DEPTH_V1_PROOF.md` |
| Gate | `make alt12-2-gate` |

## Alt-13 Summon Wave — Creative Chain & Constitutional Closure Fabric

Batch-admit nine read-only organs across constitutional creative genomes, Story Forge → Beatbox → Speakers chain lanes, and module governance posture.

| Convention | Value |
|------------|-------|
| Batch id | `alt13-summon-wave-2026-06` in LOGBOOK |
| Activation order | `ul_lineage_console_organ` → `module_governance_organ` → `recipe_module_organ` → `imagine_generator_organ` → `story_forge_lane_organ` → `beatbox_lane_organ` → `speakers_lane_organ` → `human_voice_extraction_organ` → `narrative_trust_pack_organ` |
| MVP promotion | `tools/governance/alt13_promote_mvp.py` |
| Gates | `make alt13-gate` |
| Governed promotion | `tools/governance/alt13_promote_governed.py` + `make alt13-governed-gate` |

Depends on: Alt-12 governed OTEM/predictive/execution fabric; governed constitutional genomes (`recipe_module`, `imagine_generator`, `narrative_trust_pack`, `human_voice_extraction`, `cisiv_operator_lineage_console`); live `story_forge_audio` admission path.

## Alt-13.1 Coherence Fabric Creative/Constitutional Join

| Convention | Value |
|------------|-------|
| Batch id | `alt13-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.8` + `constitutional_creative_posture[]`, `story_chain_posture[]`, `module_governance_posture[]` |
| Gate | `make alt13-1-gate` |

## Alt-13.2 Creative Chain & Module Governance Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt13-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/storyforge/STORY_CHAIN_V1_PROOF.md`, `docs/proof/platform/CONSTITUTIONAL_CREATIVE_V1_PROOF.md`, `docs/proof/platform/MODULE_GOVERNANCE_ORGAN_V1_PROOF.md` |
| Gate | `make alt13-2-gate` |

## Alt-14 Summon Wave — Route Choice & Perception Fabric

Batch-admit nine read-only organs across perception gateway, spatial/mystic lanes, and turn-level route-choice posture.

| Convention | Value |
|------------|-------|
| Batch id | `alt14-summon-wave-2026-06` in LOGBOOK |
| Activation order | `document_vision_organ` → `ui_vision_organ` → `perception_gateway_organ` → `spatial_reasoning_organ` → `mystic_engine_organ` → `perception_lane_organ` → `route_choice_organ` → `specialist_route_organ` → `provider_route_organ` |
| MVP promotion | `tools/governance/alt14_promote_mvp.py` |
| Gates | `make alt14-gate` |
| Governed promotion | `tools/governance/alt14_promote_governed.py` + `make alt14-governed-gate` |

Depends on: Alt-13 governed creative chain; live `document_vision`, `ui_vision`, `Spatial_reasoning`, `mystic_engine`, `model_routing`, `specialist_registry`, `provider_mind`; capability bridge spatial/mystic paths.

## Alt-14.1 Coherence Fabric Perception/Route Join

| Convention | Value |
|------------|-------|
| Batch id | `alt14-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.9` + `perception_posture[]`, `spatial_symbolic_posture[]`, `route_choice_posture[]` |
| Gate | `make alt14-1-gate` |

## Alt-14.2 Route Choice & Perception Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt14-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/platform/PERCEPTION_GATEWAY_V1_PROOF.md`, `docs/proof/platform/ROUTE_CHOICE_V1_PROOF.md`, `docs/proof/platform/SPATIAL_SYMBOLIC_V1_PROOF.md` |
| Gate | `make alt14-2-gate` |

## Alt-15 Summon Wave — Nova Cortex Lobe & Voice Fabric

Batch-admit nine read-only organs across executive/attention, deliberation/planning/arcs, and voice/execution/face posture.

| Convention | Value |
|------------|-------|
| Batch id | `alt15-summon-wave-2026-06` in LOGBOOK |
| Activation order | `reasoning_executive_organ` → `attention_organ` → `coherence_projection_organ` → `deliberation_organ` → `planning_organ` → `cortex_arcs_organ` → `cognitive_execution_organ` → `speaking_runtime_organ` → `nova_face_organ` |
| MVP promotion | `tools/governance/alt15_promote_mvp.py` |
| Gates | `make alt15-gate` |
| Governed promotion | `tools/governance/alt15_promote_governed.py` + `make alt15-governed-gate` |

Depends on: Alt-14 governed route/perception fabric; Alt-8 mind-plane organs; Alt-5 reflection/memory runtime organs; live Nova cortex lobes and coherence projection.

## Alt-15.1 Coherence Fabric Lobe/Voice Join

| Convention | Value |
|------------|-------|
| Batch id | `alt15-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.10` + `executive_attention_posture[]`, `deliberation_planning_posture[]`, `voice_execution_posture[]` |
| Gate | `make alt15-1-gate` |

## Alt-15.2 Nova Lobe & Voice Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt15-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/cognitive_runtime/NOVA_LOBE_V1_PROOF.md`, `docs/proof/cognitive_runtime/COHERENCE_PROJECTION_ORGAN_V1_PROOF.md`, `docs/proof/cognitive_runtime/SPEAKING_RUNTIME_ORGAN_V1_PROOF.md` |
| Gate | `make alt15-2-gate` |

## Alt-16 Summon Wave — Factory & Kinetic Fabric

Batch-admit nine read-only organs across mind fabrication, contractor lanes, and kinetic/shell posture.

| Convention | Value |
|------------|-------|
| Batch id | `alt16-summon-wave-2026-06` in LOGBOOK |
| Activation order | `ai_factory_organ` → `cogos_runtime_bridge_organ` → `wolf_rehydration_organ` → `forge_contractor_organ` → `forge_eval_organ` → `evolve_engine_organ` → `slingshot_organ` → `operator_workbench_organ` → `workflow_shell_organ` |
| MVP promotion | `tools/governance/alt16_promote_mvp.py` |
| Gates | `make alt16-gate` |
| Governed promotion | `tools/governance/alt16_promote_governed.py` + `make alt16-governed-gate` |

Depends on: Alt-15 governed Nova lobe/voice fabric; Alt-11 coding stack; Alt-10 forensics for Slingshot; live AI Factory, Slingshot, Forge/Evolve clients, CoGOS bridge, workflow shell.

## Alt-16.1 Coherence Fabric Factory/Kinetic Join

| Convention | Value |
|------------|-------|
| Batch id | `alt16-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.11` + `factory_fabrication_posture[]`, `contractor_lane_posture[]`, `kinetic_shell_posture[]` |
| Gate | `make alt16-1-gate` |

## Alt-16.2 Factory & Kinetic Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt16-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/platform/FACTORY_KINETIC_V1_PROOF.md`, `docs/proof/ai_factory/AI_FACTORY_ORGAN_V1_PROOF.md`, `docs/proof/platform/SLINGSHOT_ORGAN_V1_PROOF.md` |
| Gate | `make alt16-2-gate` |

## Alt-17 Summon Wave — Authority Shell & Protocol Fabric

Batch-admit nine read-only organs across Jarvis protocol/contracts, authority shell substrate, and response integrity posture.

| Convention | Value |
|------------|-------|
| Batch id | `alt17-summon-wave-2026-06` in LOGBOOK |
| Activation order | `jarvis_protocol_organ` → `reasoning_contract_organ` → `jarvis_reasoning_lane_organ` → `conversation_memory_organ` → `continuity_substrate_organ` → `jarvis_operator_organ` → `anti_drift_organ` → `prompt_assembly_organ` → `output_integrity_organ` |
| MVP promotion | `tools/governance/alt17_promote_mvp.py` |
| Gates | `make alt17-gate` |
| Governed promotion | `tools/governance/alt17_promote_governed.py` + `make alt17-governed-gate` |

Depends on: Alt-16 governed factory/kinetic fabric; Alt-15 reasoning executive (non-usurping); safety envelope and barebones bridge/pipeline.

## Alt-17.1 Coherence Fabric Authority/Protocol Join

| Convention | Value |
|------------|-------|
| Batch id | `alt17-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.12` + `protocol_posture[]`, `authority_shell_posture[]`, `response_integrity_posture[]` |
| Gate | `make alt17-1-gate` |

## Alt-17.2 Authority & Protocol Integrity Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt17-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/platform/AUTHORITY_PROTOCOL_INTEGRITY_V1_PROOF.md`, `docs/proof/platform/JARVIS_PROTOCOL_ORGAN_V1_PROOF.md`, `docs/proof/platform/OUTPUT_INTEGRITY_ORGAN_V1_PROOF.md` |
| Gate | `make alt17-2-gate` |

## Alt-18 Summon Wave — Project Infi Law Fabric

Batch-admit nine read-only organs across law cycle, turn admission, and governance control posture.

| Convention | Value |
|------------|-------|
| Batch id | `alt18-summon-wave-2026-06` in LOGBOOK |
| Activation order | `project_infi_state_machine_organ` → `project_infi_law_organ` → `run_ledger_binding_organ` → `chat_turn_governance_organ` → `aais_ul_substrate_organ` → `aris_integration_organ` → `governance_layer_organ` → `security_protocol_organ` → `system_guard_organ` |
| MVP promotion | `tools/governance/alt18_promote_mvp.py` |
| Gates | `make alt18-gate` |
| Governed promotion | `tools/governance/alt18_promote_governed.py` + `make alt18-governed-gate` |

Depends on: Alt-17 governed authority/protocol fabric; existing `run_ledger_organ`; **special_review_only** posture on law surfaces (no autonomous law mutation).

## Alt-18.1 Coherence Fabric Law Fabric Join

| Convention | Value |
|------------|-------|
| Batch id | `alt18-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.13` + `law_cycle_posture[]`, `turn_admission_posture[]`, `governance_control_posture[]` |
| Gate | `make alt18-1-gate` |

## Alt-18.2 Project Infi Law Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt18-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/platform/PROJECT_INFI_LAW_V1_PROOF.md`, `docs/proof/platform/CHAT_TURN_GOVERNANCE_ORGAN_V1_PROOF.md`, `docs/proof/platform/GOVERNANCE_LAYER_ORGAN_V1_PROOF.md` |
| Gate | `make alt18-2-gate` |

## Alt-19 Summon Wave — Operator Product Shell Fabric

Batch-admit nine read-only organs across product shell, operator surfaces, and composed runtime posture.

| Convention | Value |
|------------|-------|
| Batch id | `alt19-summon-wave-2026-06` in LOGBOOK |
| Activation order | `launcher_organ` → `aais_doctor_organ` → `workflow_runtime_organ` → `jarvis_console_surface_organ` → `memory_bank_surface_organ` → `dashboard_surface_organ` → `nova_landing_surface_organ` → `aais_composed_runtime_organ` → `api_gateway_organ` |
| MVP promotion | `tools/governance/alt19_promote_mvp.py` |
| Gates | `make alt19-gate` |
| Governed promotion | `tools/governance/alt19_promote_governed.py` + `make alt19-governed-gate` |

Depends on: Alt-18 governed law/admission posture; launcher maintain-only per spec §5 (read-only posture, not new product features).

## Alt-19.1 Coherence Fabric Product Shell Join

| Convention | Value |
|------------|-------|
| Batch id | `alt19-1-summon-wave-2026-06` in LOGBOOK |
| Snapshot | `operator_cognition_coherence_fabric.v1.14` + `product_shell_posture[]`, `operator_surface_posture[]`, `composed_runtime_posture[]` |
| Gate | `make alt19-1-gate` |

## Alt-19.2 Operator Product Shell Closure

| Convention | Value |
|------------|-------|
| Batch id | `alt19-2-summon-wave-2026-06` in LOGBOOK |
| Proof | `docs/proof/platform/OPERATOR_PRODUCT_SHELL_V1_PROOF.md`, `docs/proof/platform/LAUNCHER_ORGAN_V1_PROOF.md`, `docs/proof/platform/API_GATEWAY_ORGAN_V1_PROOF.md` |
| Gate | `make alt19-2-gate` |

## Activation Rule

Subsystems move through stages per
[AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md):

```text
concept → prototype → mvp → governed
```

Promotion from `docs/_future/ideas_pending/` requires (per
[ideas_pending/README.md](../_future/ideas_pending/README.md)):

1. Spec admitted into `docs/subsystems/`, `docs/runtime/`, or contracts
2. Runtime code backs the claimed behavior
3. Proof packet exists under `docs/proof/` with appropriate claim labels
4. Passing tests, schema validation, and make gate
5. Genome record updated (`governance/subsystem_genomes/<gene>.genome.v1.json`)

## Proof Posture Terminology

At concept admission:

- **`none_yet`** — claim not yet proven; default for implementation targets
- **`asserted`** — schema-coverage or doc-only claims backed by spec + schema

The informal term `asserted_none_yet` maps to **`none_yet`** in proof posture tables.
Do not add a third label enum to schemas or docs.

## Activation Order (Batches)

When admitting N ideas in one pass, assign order by:

1. Fewest dependencies on existing live subsystems first
2. Ideas that other pending ideas depend on before their dependents
3. Record in concept spec §11, MVP plan §8, and LOGBOOK outcome

## Schema Conventions

- JSON Schema draft 2020-12
- `$id`: `<snake_case>.v1`
- Required `{entity}_version` const matching `$id`
- Required `claim_label`: `asserted` | `proven` | `rejected`
- Required `cisiv_stage`: `concept` | `identity` | `structure` | `implementation` | `verification`
- CISIV helpers: [src/cisiv.py](../../src/cisiv.py)

## Golden Examples

| Idea | Concept | MVP plan | Active doc | Proof |
|------|---------|----------|------------|-------|
| CISIV Operator Lineage Console | [CISIV_OPERATOR_LINEAGE_CONSOLE.md](../_future/ideas_pending/CISIV_OPERATOR_LINEAGE_CONSOLE.md) | [CISIV_OPERATOR_LINEAGE_CONSOLE_MVP_PLAN.md](../_future/ideas_pending/CISIV_OPERATOR_LINEAGE_CONSOLE_MVP_PLAN.md) | [UL_LINEAGE_CONSOLE.md](../runtime/UL_LINEAGE_CONSOLE.md) | [UL_LINEAGE_CONSOLE_V1_PROOF.md](../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md) |
| Forensic Triangulation Ledger | [FORENSIC_TRIANGULATION.md](../_future/ideas_pending/FORENSIC_TRIANGULATION.md) | [FORENSIC_TRIANGULATION_MVP_PLAN.md](../_future/ideas_pending/FORENSIC_TRIANGULATION_MVP_PLAN.md) | [TRIANGULATION.md](../subsystems/forensics/TRIANGULATION.md) | [TRIANGULATION_V1_PROOF.md](../proof/forensics/TRIANGULATION_V1_PROOF.md) |
| Narrative Trust Pack | [NARRATIVE_TRUST_PACK.md](../_future/ideas_pending/NARRATIVE_TRUST_PACK.md) | [NARRATIVE_TRUST_PACK_MVP_PLAN.md](../_future/ideas_pending/NARRATIVE_TRUST_PACK_MVP_PLAN.md) | [NARRATIVE_TRUST_PACK.md](../subsystems/storyforge/NARRATIVE_TRUST_PACK.md) | [NARRATIVE_TRUST_PACK_V1_PROOF.md](../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md) |

## Related

- [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md)
- [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md)
- [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md)
- [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md)
- [AAIS_MODULE_GOVERNANCE_PROTOCOL.md](./AAIS_MODULE_GOVERNANCE_PROTOCOL.md)
- [AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md)
- [AAIS_DOC_PROTOCOL.md](./AAIS_DOC_PROTOCOL.md)
- [ideas_pending/README.md](../_future/ideas_pending/README.md)
