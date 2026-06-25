# CTS — Conformance Test Suite (CAS 1.0)

Validates three dimensions:

1. **Object correctness** — identity, run, span, receipt, fault
2. **Lifecycle correctness** — init → execute → finalize → receipt
3. **Governance correctness** — invariants, enforcement, faults

## Layout

```
tests/cts/
  helpers/
    schemaValidator.ts   # Ajv validator against schemas/cas-1.0.json
  cas/
    identity/
    run/
    span/
    receipt/
    fault/
    schema/              # JSON Schema conformance tests
  governance/
    invariants/
    enforcement/
  determinism/
```

Schema conformance: every CAS object type is validated against `schemas/cas-1.0.json`.
Runtime output from CRK-1 is also checked in `cas/schema/validateRuntimeOutput.test.ts`.

## Run

```bash
cd aaes-os
pnpm test:cts
```

Reference runtime: `runtime/crk1/`
