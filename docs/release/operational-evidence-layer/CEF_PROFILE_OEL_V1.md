# CEF Profile: OEL v1.0 — Operational Evidence Layer

**Status:** Specified — CEF profile  
**Parent framework:** [../cef/CEF_V1_SPECIFICATION.md](../cef/CEF_V1_SPECIFICATION.md)  
**Storage root:** `docs/release/operational-evidence-layer/`

## 1. Purpose

OEL v1.0 provides governed operational evidence for deployments, upgrades, and runtime behavior. It replaces “Version X deployed” with a constitutional evidence chain.

## 2. Evidence Chain

```text
Deployment → Evidence Record → Promotion Decision → Certificate → Stewardship
```

## 3. Required Evidence Fields

| Field | Description |
| --- | --- |
| `deploymentId` | Deployment identity |
| `commitSha` | Git commit boundary |
| `containerDigest` | Immutable image digest |
| `immutableTag` | Non-`latest` tag policy pin |
| `sbomRef` | SBOM artifact reference |
| `supplyChainFacts` | Supply-chain attestations |
| `vulnerabilityScan` | Scanner result object |
| `securityGates` | Aggregated security gate outcomes |
| `conformanceTests` | `{ passed, total }` |
| `runtimeHealth` | Liveness / readiness snapshot |
| `policyValidation.netpol` | NetworkPolicy validation |
| `policyValidation.rbac` | RBAC validation |
| `policyValidation.securityContext` | Pod securityContext validation |
| `promotionDecision` | Via CEF `promotion.decision` |
| `authority` | CAR binding |
| `signature` | Via CEF `promotion.signature` |
| `timestamp` | Via CEF `promotion.timestamp` |

Schema: [../cef/schemas/cef-oel-evidence.schema.json](../cef/schemas/cef-oel-evidence.schema.json)

## 4. Certificate Rules

1. Certificates MUST remain `DRAFT` until all gates pass.
2. Certificates MUST be immutable once promoted.
3. Certificates MUST include replay instructions for full operational reconstruction.
4. Certificates MUST be stored under `docs/release/operational-evidence-layer/`.

Baseline DRAFT certificate: [certificates/baseline-v1.0.certificate.yaml](./certificates/baseline-v1.0.certificate.yaml)

## 5. Stewardship

OEL certificates enter stewardship once promoted. Stewardship includes:

- Monitoring
- Renewal
- Revocation
- Historical replay
- Audit disclosure

See [../cef/STEWARDSHIP_PROTOCOL_V1.md](../cef/STEWARDSHIP_PROTOCOL_V1.md).

## 6. Notes

- Certificate remains DRAFT/HOLD until all gates are satisfied.
- Prevents “greenwashing” deployments.
- Ensures constitutional integrity.
