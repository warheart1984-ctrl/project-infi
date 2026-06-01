# Platform Membrane v4 Specification

| Field | Value |
|-------|-------|
| **Service ID** | `platform.membrane.v4` |
| **Doc alias** | `platform.membrane.v3.1` (non-breaking) |
| **Port** | 8090 (default) |
| **Authority** | `META_ARCHITECT_LAWBOOK.md`, MA-13 |

Canonical forward spec: [PLATFORM_MEMBRANE_V5_SPEC.md](./PLATFORM_MEMBRANE_V5_SPEC.md).

Historical: [PLATFORM_MEMBRANE_V3_SPEC.md](./PLATFORM_MEMBRANE_V3_SPEC.md) (v21–v30 fourth arc).

## Layer map

| Layer | Versions | Capability |
|-------|----------|------------|
| Substrate | v1–v7 | Orgs, jobs, artifacts, console |
| Commercial | v8–v14 | OIDC, billing, region, drift, assistant, DSL, workflows |
| Civilization | v15–v20 | Operator Mesh, Marketplace, Proof Federation |
| Fourth arc | v21–v30 | Mesh v2, Marketplace v2, Proof v2 (HMAC), Sovereign v1 |
| Fifth arc | v31–v40 | Event membrane, Marketplace v3, Proof v3, Mesh v3, Sovereign v2 |

## Proof evolution

| Generation | Signing | Registry |
|------------|---------|----------|
| v2 (v25–v28) | HMAC-SHA256 shared secret | `proof_runners` optional enforce |
| v3 (v35–v36) | Ed25519 per-runner + HMAC dev fallback | `public_key_pem` on enroll |

## Primitives (v4)

| Primitive | Schema / module |
|-----------|-----------------|
| webhook_subscription | `platform/schemas/webhook_subscription.v1.json` |
| attestation_bundle | `platform/schemas/proof_attestation_bundle.v1.json` |
| listing_review | store `listing_reviews` |
| mesh_event_cursor | query param `cursor` on mesh events |

## MA-13 boundary

- **Webhooks:** notify only; no job actuation without operator consent.
- **Mesh:** routing and queues; no autonomous on-call execution.
- **Auditor role:** read-only scopes; no `jobs:submit`.

## Claim taxonomy

| Arc | Local | Cross-machine |
|-----|-------|---------------|
| v21–v30 | asserted — `platform-v4-smoke` | proven — tertiary CI hash quorum |
| v31–v40 | asserted — `platform-v5-smoke` | proven — proof v3 attestation POST + events delivery tests |

## Related contracts

- [PLATFORM_EVENT_MEMBRANE_CONTRACT.md](../subsystems/platform/PLATFORM_EVENT_MEMBRANE_CONTRACT.md)
- [OPERATOR_MESH_CONTRACT.md](../subsystems/platform/OPERATOR_MESH_CONTRACT.md) (§v3)
- [WORKFLOW_MARKETPLACE_SCHEMA.md](../subsystems/platform/WORKFLOW_MARKETPLACE_SCHEMA.md) (§v3)
- [PROOF_FEDERATION_PROTOCOL.md](../subsystems/platform/PROOF_FEDERATION_PROTOCOL.md) (§v3)
- [PLATFORM_API_CONTRACT.md](../subsystems/platform/PLATFORM_API_CONTRACT.md) (v4)

## Verification

```bash
python .github/scripts/check-platform-v4-spec-governance.py
make platform-v5-gate
make platform-v5-smoke
```
