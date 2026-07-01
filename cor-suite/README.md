# COR Suite (project-infi)

Self-governing COR-1.0 observability for the AAES-OS substrate.

## Commands

Run from `project-infi/cor-suite`:

```bash
npm install
npm run car:bootstrap  # initial CAR population (once, then curate)
npm run validate       # CAV-1.0 — validate car-1.0.json
npm run hygiene        # Repo hygiene scan
npm run cor            # Generate COR state vector (from CAR)
npm run analyze        # Proof analysis
npm run maturity       # Maturity vector
npm run govern         # Governance receipt
npm run pipeline       # Full pipeline
npm run ci-gate        # CI failure gate (after pipeline steps)
```

## CAR-1.0

Canonical Artifact Registry: `car/car-1.0.json`. See [car/README.md](./car/README.md).

COR reads **only from CAR** — no filesystem scan for canonical artifacts.

## Outputs

Artifacts land in `cor-suite/out/`:

- `cav-validation.json`
- `cor-state.json`
- `proof-analysis.json`
- `maturity-vector.json`
- `governance-receipt.json`
- `repo-hygiene-status.json`

## Consumption

**skillzmcgee** (cockpit) fetches these via `cor-client/` — it does not run governance locally.

## Spec

JSON schemas and layer contracts: `cor-suite/spec/`

- [CAR-1.0-Registry.md](./spec/CAR-1.0-Registry.md) · [CAV-1.0-Validation.md](./spec/CAV-1.0-Validation.md)
- [COR-Suite-Spec-1.0.md](./spec/COR-Suite-Spec-1.0.md) · [RFC-COR-Suite-1.0.md](./spec/RFC-COR-Suite-1.0.md)
- [Release criteria v1.0](./governance/release-criteria/v1.0.md)

Governance charter: `cor-suite/governance/charter/`.
