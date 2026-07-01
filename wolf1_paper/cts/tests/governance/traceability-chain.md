# CTS-GOV-TRACE-001 — Complete Traceability Chains

## Rule

Every normative requirement MUST have a complete, machine-verifiable traceability chain:

**Requirement → ADR → Reference Implementation → CTS → Evidence Ledger → Benchmark/Replication** (where applicable).

## Checks

- `scripts/validate_traceability_chain.py` MUST pass with zero failures (CI).
- `scripts/validate_traceability_chain.mjs` is the portable Node equivalent for local dev without Python.
- Any requirement marked `benchmark_required: true` MUST have at least one benchmark entry in `registries/benchmarks.yaml`.
- CI MUST fail if any requirement is missing one or more links.

## Expected Result

- **PASS:** All requirements have full chains.
- **FAIL:** CI reports incomplete chains and blocks merge.

## Run locally

```bash
python scripts/validate_traceability_chain.py
# or
bash scripts/enforce_governance.sh
```
