# Certification Engine v1.0

**Status:** Specified — CEF v1.0 companion  
**Parent:** [CEF_V1_SPECIFICATION.md](./CEF_V1_SPECIFICATION.md)

## 1. Purpose

The Certification Engine is the constitutional promotion mechanism for evidence. It ensures that certificates are:

- Valid
- Verified
- Replayable
- Auditable
- Governed

## 2. Promotion Lifecycle

1. Evidence Collection  
2. Verification Gates  
3. Authority Check (CAR)  
4. Promotion Decision  
5. Signature  
6. Certificate Creation  
7. Publication  
8. Stewardship  

Detailed stages: [PROMOTION_WORKFLOW_V1.md](./PROMOTION_WORKFLOW_V1.md)

## 3. Verification Gates

All gates MUST pass before promotion:

| Gate | Meaning |
| --- | --- |
| Integrity | Evidence identity and inputs are intact |
| Completeness | Required profile fields present |
| Security | SBOM, supply chain, vulnerability (as required by profile) |
| Conformance | Declared tests meet threshold |
| Policy | Profile policy gates (e.g. NetPol / RBAC / securityContext for OEL) |
| Replay | Deterministic reconstruction instructions present and valid |
| Audit | Visibility / disclosure metadata present |

## 4. Certificate Structure

| Field | Description |
| --- | --- |
| `certificateId` | Unique certificate identity |
| `evidenceRef` | Reference to CEF evidence object |
| `authorityRef` | CAR / authority binding |
| `signature` | Promotion signature |
| `version` | Certificate version |
| `replayInstructions` | Full reconstruction path |
| `auditMetadata` | Visibility and disclosure |
| `stewardshipState` | unpromoted \| active \| renewal_pending \| revoked \| historical |
| `status` | DRAFT \| ACTIVE \| REVOKED \| HISTORICAL |
| `profile` | CEF profile id |
| `promotion` | decision, signature, timestamp |

Schema: [schemas/cef-certificate.schema.json](./schemas/cef-certificate.schema.json)

## 5. Revocation

Certificates may be revoked only through governed authority and MUST produce a revocation evidence record.

## 6. Immutability rule

Once `status` is `ACTIVE` (promoted), certificate fields MUST NOT be modified. Corrections require a new evidence version, new promotion, and new certificate id — with lineage to the prior certificate.
