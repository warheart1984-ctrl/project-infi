# CAV-1.0 Validation

**Layer:** Validation  
**RFC:** [RFC-COR-Suite-1.0.md](./RFC-COR-Suite-1.0.md)  
**Schema:** [cav-validation.schema.json](./cav-validation.schema.json)

## Identity

CAV-1.0 (Canonical Artifact Validation) verifies the integrity of CAR-1.0 and every registered artifact.

## Purpose

Validation is **separate from measurement and governance**. CAV answers: “Is the canonical registry well-formed and consistent with the repository?” It MUST NOT make governance decisions or interpret measurements as approve/reject.

## Inputs

- `car-1.0.json`
- [car-1.0.schema.json](./car-1.0.schema.json)
- File contents at each registered `path`

## Checks

1. **Schema conformance** — registry and entries match CAR-1.0 JSON Schema.
2. **Path existence** — every active artifact path exists in the repository.
3. **Hash integrity** — stored `hash` matches SHA-256 of file contents.
4. **Unique IDs** — no duplicate `id` values.
5. **Lifecycle consistency** — retired entries have `retiredAt`; deprecated entries SHOULD have `supersededBy`.
6. **Link integrity** — `supersedes`, `supersededBy`, `related` reference known IDs.

## Output classification

### Blocking findings

MUST fail CI and MUST block COR measurement when present:

- Invalid canonical artifacts (schema violations)
- Broken provenance chains (missing paths, hash mismatches)
- Missing required canonical artifacts (policy-defined required entries)
- Duplicate IDs
- Retired status without required lifecycle fields

### Advisory findings

MUST NOT alone block release; surfaced to stewards and Analysis:

- Deprecated authorities with valid successors
- Non-critical verification gaps
- High dependency-risk nodes (when cross-referenced with DRA)
- Research claims or exploratory artifacts marked draft

## Output artifact

- **File:** `cor-suite/out/cav-validation.json`
- **Fields:** `cavVersion`, `carRef`, `generatedAt`, `valid`, `blockingCount`, `advisoryCount`, `findings[]`

Each finding: `findingId`, `category`, `severity`, `blocking`, `message`, optional `artifactId` / `path`.

## Prohibitions

CAV-1.0 MUST NOT:

- make governance decisions (approve, reject, freeze)
- mutate CAR or repository files
- perform counterfactual analysis
- replace COR structural integrity reporting (CAV validates registry; COR reports constitutional state derived from CAR)

## Pipeline position

```
Repo Hygiene → CAV-1.0 validate → COR / CSR / DRA measure → Proof Analysis → Governance → Communication
```

COR-1.0 MUST NOT run when CAV reports blocking findings.

## Implementation (project-infi)

- Validator: `cor-suite/src/car/validate.ts`
- CLI: `npm run validate` / `cor-suite validate`
- CI gate: `cor-suite/src/cli/ci-gate.ts`
