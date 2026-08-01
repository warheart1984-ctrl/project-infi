# Constitutional Evidence Framework (CEF) v1.0

One evidence architecture. Specialized profiles. Governed promotion.

**Invariant:** No claim may exceed its evidence.

## Canonical documents

| Document | Path |
| --- | --- |
| **Charter** | [CEF_V1_CHARTER.md](./CEF_V1_CHARTER.md) |
| **Specification** | [CEF_V1_SPECIFICATION.md](./CEF_V1_SPECIFICATION.md) |
| **Architecture diagram** | [CEF_V1_ARCHITECTURE.txt](./CEF_V1_ARCHITECTURE.txt) |
| **Certification Engine** | [CERTIFICATION_ENGINE_V1.md](./CERTIFICATION_ENGINE_V1.md) · stub `@aaes-os/cef-certification` |
| **Stewardship** | [STEWARDSHIP_PROTOCOL_V1.md](./STEWARDSHIP_PROTOCOL_V1.md) · stub `@aaes-os/cef-stewardship` |
| **cef-core (runtime validation)** | [`packages/cef-core`](../../../packages/cef-core/README.md) |
| **Promotion Workflow** | [PROMOTION_WORKFLOW_V1.md](./PROMOTION_WORKFLOW_V1.md) |
| **Stewardship Protocol** | [STEWARDSHIP_PROTOCOL_V1.md](./STEWARDSHIP_PROTOCOL_V1.md) |
| **Implementation Plan** | [CEF_V1_IMPLEMENTATION_PLAN.md](./CEF_V1_IMPLEMENTATION_PLAN.md) |
| **Conformance Suite** | [conformance/CEF_V1_CONFORMANCE_SUITE.md](./conformance/CEF_V1_CONFORMANCE_SUITE.md) |
| **Stewardship Dashboard** | [observability/CEF_V1_STEWARDSHIP_DASHBOARD.md](./observability/CEF_V1_STEWARDSHIP_DASHBOARD.md) |

## Schemas

| Schema | Path |
| --- | --- |
| Core evidence | [schemas/cef-core-evidence.schema.json](./schemas/cef-core-evidence.schema.json) |
| OEL profile | [schemas/cef-oel-evidence.schema.json](./schemas/cef-oel-evidence.schema.json) |
| Certificate | [schemas/cef-certificate.schema.json](./schemas/cef-certificate.schema.json) |
| Profile registry | [cef-profile-registry.json](./cef-profile-registry.json) |

## Profiles

```text
CEF
├── CREC       Research Evidence
├── OEL        Operational Evidence
├── CEL        Linguistic / Constitutional Evidence
├── Security   SBOM, supply chain, vulnerability, policy
├── ModelEval  Benchmarks, risk, uncertainty, lineage
└── Certification Engine → Certificate → Stewardship
```

- OEL profile: [../operational-evidence-layer/CEF_PROFILE_OEL_V1.md](../operational-evidence-layer/CEF_PROFILE_OEL_V1.md)
- Baseline Certificate DRAFT: [../operational-evidence-layer/certificates/baseline-v1.0.certificate.yaml](../operational-evidence-layer/certificates/baseline-v1.0.certificate.yaml)

## Architecture (summary)

```text
Profiles → Certification Engine → Certificate → Stewardship
```

Full ASCII: [CEF_V1_ARCHITECTURE.txt](./CEF_V1_ARCHITECTURE.txt)

## Legacy note

Earlier CEF v0.1 draft materials in this folder are superseded by **CEF v1.0** documents above. Prefer Charter + Specification as normative.
