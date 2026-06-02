# Adaptive Lane Organ

CISIV stage: **verification**

Status: **governed** (Alt-6 summon wave `alt6-summon-wave-2026-06`)

## Purpose

Wake Tier 5 **operator-weighted lanes** from genome DNA into a live runtime registry.
The organ merges `governance.operator_lanes` across governed genomes with the Operator
Profile authority lane and exposes an inspectable snapshot for Jarvis and the Capability
Service Bridge.

## Contract

Schema: [schemas/adaptive_lane_organ.v1.json](../../../schemas/adaptive_lane_organ.v1.json)

Parent law: [AAIS_ADAPTIVE_GOVERNANCE.md](../../contracts/AAIS_ADAPTIVE_GOVERNANCE.md)

## Runtime Surface

| Kind | Path |
|------|------|
| module | `src/adaptive_lane_organ.py` |
| API | `GET /api/jarvis/adaptive-lanes/status` |
| boot | `Tier5Governance.wake_lanes()` after Alt-4 genome validation |
| persistence | `.runtime/governance/adaptive_lanes.json` |
| gate | `make adaptive-lane-gate` |

## Integration

- **Operator Profile Organ** — supplies `authority_lane`
- **Capability Service Bridge** — resolves lane before execute; blocks policy caps on lane mismatch
- **Adaptive Engine (Tier 5)** — health report includes `adaptive_lanes_awakened`

## Proof

[ADAPTIVE_LANE_GOVERNED_PROOF.md](../../proof/platform/ADAPTIVE_LANE_GOVERNED_PROOF.md)

MVP history: [ADAPTIVE_LANE_V1_PROOF.md](../../proof/platform/ADAPTIVE_LANE_V1_PROOF.md)

## Related

- [OPERATOR_PROFILE_ORGAN.md](./OPERATOR_PROFILE_ORGAN.md)
- [CAPABILITY_SERVICE_BRIDGE.md](./CAPABILITY_SERVICE_BRIDGE.md)
