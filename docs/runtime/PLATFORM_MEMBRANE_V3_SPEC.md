# Platform Membrane v3 Specification

| Field | Value |
|-------|-------|
| **Service ID** | `platform.membrane.v3` |
| **Port** | 8090 (default) |
| **Authority** | `META_ARCHITECT_LAWBOOK.md`, MA-13 Stage 2 Copilot Doctrine |

Canonical forward spec: [PLATFORM_MEMBRANE_V4_SPEC.md](./PLATFORM_MEMBRANE_V4_SPEC.md).

Runtime primer: [PLATFORM_MEMBRANE.md](./PLATFORM_MEMBRANE.md).

## Layer map

| Layer | Versions | Capability |
|-------|----------|------------|
| Substrate | v1–v7 | Orgs, jobs, artifacts, console, deploy |
| Commercial | v8–v14 | OIDC, billing, region, drift, assistant, DSL, workflows |
| Civilization | v15–v20 | Operator Mesh, Marketplace, Proof Federation |
| Fourth arc | v21–v30 | Mesh v2 (SSE, policy), Marketplace v2, Proof v2, Sovereign plane |

## Primitives

| Primitive | Schema / contract |
|-----------|-------------------|
| org | store `orgs` |
| job | `platform.platform_job.v1` |
| artifact_ref | `platform.platform_artifact_ref.v1` |
| workflow_listing | `platform.workflow_listing.v1` |
| proof_attestation | `platform.proof_attestation.v1` |
| mesh_event | `platform.mesh_event.v1` |
| handoff_bundle | `platform.handoff_bundle.v1` |

## MA-13 boundary

| Class | Membrane must not |
|-------|-------------------|
| I — Usurpation | Invent operator goals; auto-execute Stage 3 |
| II — Distortion | Drop subsystem constraints on route |
| III — Leakage | Cross-org reads; hidden side effects |

- **Operator Mesh:** operational routing only (assignment, handoff).
- **Assistant:** read-only synthesis ([`platform/assistant/`](../platform/assistant/)).
- **Jarvis:** `src/api.py` remains cognition executive; no imports from platform into cognition paths.

## Claim taxonomy

| Claim | Meaning |
|-------|---------|
| asserted | Single-machine pytest or local gate |
| proven | Cross-machine replay / attestation quorum CI green |
| rejected | Gate or replay failure |

## Related contracts

- [OPERATOR_MESH_CONTRACT.md](../subsystems/platform/OPERATOR_MESH_CONTRACT.md)
- [WORKFLOW_MARKETPLACE_SCHEMA.md](../subsystems/platform/WORKFLOW_MARKETPLACE_SCHEMA.md)
- [PROOF_FEDERATION_PROTOCOL.md](../subsystems/platform/PROOF_FEDERATION_PROTOCOL.md)
- [PLATFORM_API_CONTRACT.md](../subsystems/platform/PLATFORM_API_CONTRACT.md) (v3)

## Verification

```bash
python .github/scripts/check-platform-v3-spec-governance.py
make platform-v4-gate
```
