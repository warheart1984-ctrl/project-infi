# Tutorial 5 — Running the Conformance Test Suite (CTS)

## Purpose

CTS validates invariant compliance and deterministic execution.

## Run CTS

```bash
# AAES-OS spine
cd aaes-os && pnpm test

# CRK-1 Python CTS
pytest tests/crk1 -q
```

## Interpreting failures

| Signal | Meaning |
|--------|---------|
| `INV.*` fault | Constitutional violation |
| Determinism mismatch | Receipt drift between runs |
| CTS skip | Missing fixture or env |

## Fixing violations

1. Read fault message and invariant ID
2. Inspect FaultJournal / ledger entry
3. Fix transition or payload
4. Re-run CTS until green

## CI

CTS runs on every PR via `.github/workflows/aaes-os-cts-ci.yml`.
