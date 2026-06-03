# Operator Cognition Coherence Fabric

CISIV stage: **implementation**

Status: **governed** (Alt-7 / Alt-7.1 / Alt-7.2 batches through `alt7-2-summon-wave-2026-06`)

## Purpose

Read-only **coherence health snapshot** joining operator profile, awakened lanes, and
envelope posture. The fabric coordinates Alt-5 profile/envelope organs with Alt-6 lane
wake without adding execution authority.

## Contract

Schema: [schemas/operator_cognition_coherence_fabric.v1.2.json](../../../schemas/operator_cognition_coherence_fabric.v1.2.json)

Parent law: [AAIS_ADAPTIVE_GOVERNANCE.md](../../contracts/AAIS_ADAPTIVE_GOVERNANCE.md)

## Stabilization Planes

| Plane | Source | Field |
|-------|--------|-------|
| Profile | `operator_profile_organ` | `authority_lane`, `profile_posture` |
| Lanes | `adaptive_lane_organ` | `resolved_lane`, `lane_awakened` |
| Envelopes | bridge / pipeline / memory / safety | `envelope_governance_modes[]` |
| Runtime posture | reflection + memory runtime organs | `runtime_posture[]` |

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
