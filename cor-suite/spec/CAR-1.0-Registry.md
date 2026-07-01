# CAR-1.0 Registry

**Layer:** Canonical  
**RFC:** [RFC-COR-Suite-1.0.md](./RFC-COR-Suite-1.0.md)  
**Schema:** [car-1.0.schema.json](./car-1.0.schema.json)

## Identity

CAR-1.0 (Canonical Artifact Registry) is the **single source of constitutional truth** for a governed repository.

## Purpose

Every canonical object — requirement, specification, implementation, verification, evidence, schema, governance receipt — MUST be explicitly registered. Downstream layers read **only from CAR-1.0**, not from ad-hoc repository scans.

## Registry artifact

- **File:** `cor-suite/car/car-1.0.json` (project-infi)
- **Version field:** `carVersion` (e.g. `"1.0.0"`)
- **Timestamp:** `generatedAt` (ISO 8601)

## Artifact entry (required fields)

Each entry in `artifacts[]` MUST include:

| Field | Description |
|-------|-------------|
| `id` | Stable identifier (e.g. `RUNLEDGER.REQ-001`) |
| `namespace` | Requirement namespace (e.g. `RUNLEDGER`, `TRACEBUS`, `GOV`) |
| `kind` | `requirement` \| `specification` \| `implementation` \| `verification` \| `evidence` \| `governance_receipt` \| `schema` \| `registry` |
| `version` | Semver or document version |
| `status` | `draft` \| `active` \| `deprecated` \| `retired` |
| `path` | Repo-relative path to content |
| `hash` | SHA-256 of file contents |

Optional but recommended: `authority`, `schemaRef`, `lifecycle` (`createdAt`, `updatedAt`, `deprecatedAt`, `retiredAt`), `links` (`supersedes`, `supersededBy`, `related`).

## Authoring workflow

1. Create the artifact on disk (spec, impl, test, evidence, schema, or receipt).
2. Assign ID: `{NAMESPACE}.{KIND_PREFIX}-{NNN}`.
3. Edit `car-1.0.json`: add entry with metadata and content hash.
4. Run CAV-1.0 validation before any measurement or governance step.

Bootstrap helper (non-normative): `npm run car:bootstrap` in project-infi/cor-suite scans known namespace patterns to populate an initial registry; stewards MUST curate before release.

## Lifecycle

- **Deprecate:** `status: "deprecated"`, set `deprecatedAt`, add `links.supersededBy`.
- **Retire:** `status: "retired"`, set `retiredAt`.
- **Supersede:** link old and new IDs via `supersedes` / `supersededBy`.

Governance receipts MUST be registered as `kind: "governance_receipt"` after steward decisions.

## Prohibitions

CAR-1.0 MUST NOT:

- be inferred by measurement layers
- be mutated by COR, CSR, DRA, Proof Analysis, or Communication layers
- omit hash or path for active canonical artifacts

Changes to CAR are **governed edits** to the registry file, not side effects of downstream tooling.

## Implementation (project-infi)

- Registry: `cor-suite/car/car-1.0.json`
- Bootstrap: `cor-suite/src/car/bootstrap.ts`
- Load/save: `cor-suite/src/car/registry.ts`
