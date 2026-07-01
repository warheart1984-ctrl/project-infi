# CAR-1.0 — Canonical Artifact Registry

CAR is the **single source of truth** for constitutional artifacts in project-infi. COR-1.0, CSR-1.0, and DRA-1.0 read from CAR only — they do not scan the repo for canonical paths.

## Registry file

```
cor-suite/car/car-1.0.json
```

Schema: `cor-suite/spec/car-1.0.schema.json`

## Workflow

### 1. Author an artifact

Create spec, implementation, test, evidence, schema, or governance receipt on disk.

Assign an ID: `{NAMESPACE}.{KIND}-{NNN}` (e.g. `RUNLEDGER.REQ-001`, `RUNLEDGER.IMPL-042`).

### 2. Register in CAR

Edit `car/car-1.0.json`:

- `id`, `namespace`, `kind`, `version`, `status`, `path`
- `hash` — SHA-256 of file contents
- `lifecycle.createdAt` / `updatedAt`
- `links.supersedes` / `supersededBy` for lifecycle changes

### 3. Bootstrap (initial population)

Scan repo and generate registry entries from known namespace patterns:

```bash
npm run car:bootstrap
```

This creates requirement stubs under `car/requirements/` and registers implementation/spec/verification artifacts. **Curate** the registry after bootstrap — remove noise, set authorities, link requirements.

### 4. Validate (CAV-1.0)

```bash
npm run validate
```

Checks:

| Severity | Check |
|----------|--------|
| Blocking | Schema violations, missing paths, hash mismatches, duplicate IDs, retired without `retiredAt` |
| Advisory | Deprecated without `supersededBy`, broken `links` |

Output: `out/cav-validation.json`

### 5. Measure (COR / CSR / DRA)

```bash
npm run cor        # builds COR state vector from CAR
npm run pipeline   # hygiene → validate → cor → analyze → maturity → govern
```

COR groups CAR entries by namespace into requirements and attaches spec/impl/verification/evidence by `kind`.

### 6. Lifecycle

- **Deprecate:** `status: "deprecated"`, set `deprecatedAt`, add `links.supersededBy`
- **Retire:** `status: "retired"`, set `retiredAt`
- **Supersede:** link old/new IDs via `supersedes` / `supersededBy`

Governance receipts can be registered as `kind: "governance_receipt"` artifacts after steward decisions.

## Kinds

`requirement` | `specification` | `implementation` | `verification` | `evidence` | `governance_receipt` | `schema` | `registry`

## Namespaces

| Prefix | Namespace |
|--------|-----------|
| `aaes-os/packages/runledger/` | RUNLEDGER |
| `aaes-os/packages/trace-bus/` | TRACEBUS |
| `aaes-os/packages/aaes-governance/` | GOV |
| `aaes-os/packages/ucr-runtime/` | UCR |
| `operator-surface/` | OPSURF |
| `frontend/` | UI |

See `src/cor/requirement-map.ts` for the full table.
