# AAES-OS v1.0 — Evidence Ledger

Tracks evidence supporting every architectural claim. Claims progress through four evidence levels:

1. **Hypothesis** — Concept defined, no implementation
2. **Internally Validated** — Supported by automated tests
3. **Independently Replicated** — Validated by external team
4. **Operational** — Demonstrated in real deployments

---

## Evidence Ledger

| Claim | Supporting Artifact | Test / Benchmark | Evidence Level | Replication Status | Notes |
|-------|---------------------|------------------|----------------|---------------------|-------|
| CRK-1 produces deterministic receipts for identical inputs | `packages/ucr-runtime`, `packages/runledger` | `tools/validateDeterministicReplay.ts`, CTS | Hypothesis | None | Pending full determinism gate |
| CAS 1.0 is fully specified and independently implementable | CAS Spec + CTS | Independent implementation passes CTS | Hypothesis | None | CTS must stabilize first |
| Governance Engine enforces invariants deterministically | `packages/aaes-governance` | CTS invariant tests | Hypothesis | None | Invariants under development |
| CEP can execute CDP-1 end-to-end | `cep/experimentOrchestrator.ts` | CDP-1 minimal run | Hypothesis | None | CEP scaffold added |
| CDP-1 benchmark is reproducible by external teams | `benchmarks/cdp1/`, `replication/` | External replication | Hypothesis | None | Requires CEP + packaging |
| All architectural claims are backed by executable artifacts | Entire repo | Release gates | Hypothesis | None | Dashboard governs readiness |

---

## How to Update

For each claim:

1. Add or update the **supporting artifact**
2. Link the **test or benchmark**
3. Update the **evidence level**
4. Update **replication status**
5. Add notes for any gaps

This ledger is the scientific backbone of AAES-OS v1.0.
