# Operator Cognition Coherence Fabric

CISIV stage: **implementation**

Status: **governed** (Alt-7 through Alt-16.1 batches through `alt16-1-summon-wave-2026-06`)

## Purpose

Read-only **coherence health snapshot** joining operator profile, awakened lanes, and
envelope posture. The fabric coordinates Alt-5 profile/envelope organs with Alt-6 lane
wake without adding execution authority.

## Contract

Schema: [schemas/operator_cognition_coherence_fabric.v1.11.json](../../../schemas/operator_cognition_coherence_fabric.v1.11.json)

Parent law: [AAIS_ADAPTIVE_GOVERNANCE.md](../../contracts/AAIS_ADAPTIVE_GOVERNANCE.md)

## Stabilization Planes

| Plane | Source | Field |
|-------|--------|-------|
| Profile | `operator_profile_organ` | `authority_lane`, `profile_posture` |
| Lanes | `adaptive_lane_organ` | `resolved_lane`, `lane_awakened` |
| Envelopes | bridge / pipeline / memory / safety | `envelope_governance_modes[]` |
| Runtime posture | reflection + memory runtime organs | `runtime_posture[]` |
| Mind posture | Alt-8 witness + narrative + intent organs | `mind_posture[]` |
| Infrastructure posture | Alt-9 phase gate + predictor + invariant organs | `infrastructure_posture[]` |
| Memory governance posture | Alt-10 verification + memory path + knowledge authority organs | `memory_governance_posture[]` |
| Forensics posture | Alt-10 scorpion + mechanic + triangulation organs | `forensics_posture[]` |
| Immune observe posture | Alt-10 immune observe + policy + predictor bridge organs | `immune_observe_posture[]` |
| Authority trace posture | Alt-11 cognitive bridge + event chain + tracing spine organs | `authority_trace_posture[]` |
| Mission boundary posture | Alt-11 mission board + ARIS boundary + capability module organs | `mission_boundary_posture[]` |
| Coding posture | Alt-11 patchforge + change scope + patch verification organs | `coding_posture[]` |
| OTEM lane posture | Alt-12 OTEM bounded + direct challenge + orchestration spine organs | `otem_lane_posture[]` |
| Predictive lane posture | Alt-12 health sentinel + realtime lane + V8 runtime organs | `predictive_lane_posture[]` |
| Execution depth posture | Alt-12 patch apply + execution preview + run ledger organs | `execution_depth_posture[]` |
| Constitutional creative posture | Alt-13 UL lineage + recipe + imagine + HVE + NTP organs | `constitutional_creative_posture[]` |
| Story chain posture | Alt-13 Story Forge + Beatbox + Speakers lane organs | `story_chain_posture[]` |
| Module governance posture | Alt-13 module governance organ | `module_governance_posture[]` |
| Perception posture | Alt-14 document + UI vision + perception gateway organs | `perception_posture[]` |
| Spatial symbolic posture | Alt-14 spatial + mystic + perception lane organs | `spatial_symbolic_posture[]` |
| Route choice posture | Alt-14 route + specialist + provider route organs | `route_choice_posture[]` |
| Executive attention posture | Alt-15 reasoning executive + attention + coherence projection organs | `executive_attention_posture[]` |
| Deliberation planning posture | Alt-15 deliberation + planning + cortex arcs organs | `deliberation_planning_posture[]` |
| Voice execution posture | Alt-15 cognitive execution + speaking runtime + nova face organs | `voice_execution_posture[]` |
| Factory fabrication posture | Alt-16 AI Factory + CoGOS bridge + Wolf rehydration organs | `factory_fabrication_posture[]` |
| Contractor lane posture | Alt-16 Forge contractor + ForgeEval + Evolve Engine organs | `contractor_lane_posture[]` |
| Kinetic shell posture | Alt-16 Slingshot + operator workbench + workflow shell organs | `kinetic_shell_posture[]` |

## Runtime Surface

| Kind | Path |
|------|------|
| module | `src/operator_cognition_coherence_fabric.py` |
| API | `GET /api/jarvis/coherence-fabric/status` |
| gate | `make coherence-fabric-gate`, `make alt7-gate`, `make alt7-governed-gate`, `make alt7-1-gate`, `make alt7-2-gate` |
| mutation | `make coherence-fabric-mutation-gate` (MP-OCCF-001) |
| projection | `OperatorGovernanceCoherenceModule` in `jarvis_modular.py` |
| pipeline guard | `evaluate_pipeline_coherence()` + `coherence_protocol` on trace |
| hard block | `assert_coherence_allows_turn()` — `AAIS_COHERENCE_HARD_BLOCK=1` (default) |
| status query | `GET /api/jarvis/coherence-fabric/status?session_id=` for live pipeline join |

## Integration

- **Operator Profile Organ** — authority lane source
- **Adaptive Lane Organ** — lane resolution and fabric alignment
- **Capability Service Bridge** — live bridge envelope `governance_mode`
- **Safety Envelope Organ** — halt vs strict posture
- **Jarvis Memory Board / Governed Pipeline** — idle baseline envelope posture

## Proof

- MVP: [OPERATOR_COGNITION_COHERENCE_FABRIC_V1_PROOF.md](../../proof/platform/OPERATOR_COGNITION_COHERENCE_FABRIC_V1_PROOF.md)
- Governed: [OPERATOR_COGNITION_COHERENCE_FABRIC_GOVERNED_PROOF.md](../../proof/platform/OPERATOR_COGNITION_COHERENCE_FABRIC_GOVERNED_PROOF.md)

## Related

- [OPERATOR_PROFILE_ORGAN.md](./OPERATOR_PROFILE_ORGAN.md)
- [ADAPTIVE_LANE_ORGAN.md](./ADAPTIVE_LANE_ORGAN.md)
- [SAFETY_ENVELOPE_ORGAN.md](./SAFETY_ENVELOPE_ORGAN.md)
- [NOVA_COHERENCE_PROJECTION.md](../../runtime/NOVA_COHERENCE_PROJECTION.md)
