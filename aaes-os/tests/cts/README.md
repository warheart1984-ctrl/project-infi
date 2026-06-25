# CTS — Conformance Test Suite (CAS 1.0)

Validates three dimensions:

1. **Object correctness** — identity, run, span, receipt, fault
2. **Lifecycle correctness** — init → execute → finalize → receipt
3. **Governance correctness** — invariants, enforcement, faults

## Layout

```
tests/cts/
  cas/
    identity/
    run/
    span/
    receipt/
    fault/
  governance/
    invariants/
    enforcement/
  determinism/
```

## Run

```bash
cd aaes-os
pnpm test:cts
```

Reference runtime: `runtime/crk1/`
