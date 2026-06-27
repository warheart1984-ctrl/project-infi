# AAES-OS v1.0 - Evidence Ledger

Tracks evidence supporting AAES-OS v1.0 claims. The ledger follows the project-wide [Evidence Claim Discipline](../docs/aaes-os/architecture/EVIDENCE_CLAIM_DISCIPLINE.md): documents must distinguish architectural objectives, specified guarantees, empirical claims, and research hypotheses.

## Claim Classes

| Class | Meaning | Ledger requirement |
|-------|---------|--------------------|
| Architectural objective | What the system is designed to enable | Label as design intent; do not treat as proven by implementation alone |
| Specified guarantee | Behavior a conforming Version 1.0 implementation must provide | Link to normative specification, CTS coverage, and release gate |
| Empirical claim | Behavior demonstrated by tests, replay validation, reproducibility runs, or implementation evidence | Link receipts, traces, test runs, and benchmark artifacts |
| Research hypothesis | Promising architectural pattern still being evaluated across domains | Keep explicitly marked as hypothesis until replicated evidence supports promotion |

## Evidence Levels

Claims progress through four evidence levels:

1. **Hypothesis** - Concept defined, no implementation
2. **Internally Validated** - Supported by automated tests
3. **Independently Replicated** - Validated by external team
4. **Operational** - Demonstrated in real deployments

## Verification Terms

**Replayability** means the reference implementation reproduces the same result from the same recorded evidence.

**Independent verifiability** means a separate implementation reaches the same result using only the specification and recorded artifacts.

Replay validation can move an empirical claim toward internal validation. It does not establish independent verification unless a separate implementation boundary is crossed.

---

## Evidence Ledger

| Claim | Claim Class | Supporting Artifact | Test / Benchmark | Evidence Level | Replication Status | Notes |
|-------|-------------|---------------------|------------------|----------------|---------------------|-------|
| CRK-1 produces deterministic receipts for identical inputs | Specified guarantee | `packages/ucr-runtime`, `packages/runledger` | `tools/validateDeterministicReplay.ts`, CTS | Hypothesis | None | Pending full determinism gate |
| CAS 1.0 is fully specified and independently implementable | Specified guarantee | CAS Spec + CTS | Independent implementation passes CTS | Hypothesis | None | CTS must stabilize first |
| Governance Engine enforces invariants deterministically | Specified guarantee | `packages/aaes-governance` | CTS invariant tests | Hypothesis | None | Invariants under development |
| CEP can execute CDP-1 end-to-end | Engineering contribution | `cep/experimentOrchestrator.ts` | CDP-1 minimal run | Hypothesis | None | CEP scaffold added |
| CDP-1 benchmark is reproducible by external teams | Empirical claim | `benchmarks/cdp1/`, `replication/` | External replication | Hypothesis | None | Requires CEP + packaging |
| All specified guarantees and empirical claims are backed by executable artifacts | Release objective | Entire repo | Release gates | Hypothesis | None | Dashboard governs readiness; architectural objectives and research hypotheses must remain labeled |

---

## How to Update

For each claim:

1. Assign the **claim class**
2. Add or update the **supporting artifact**
3. Link the **test or benchmark**
4. Update the **evidence level**
5. Update **replication status**
6. Add notes for any gaps

This ledger is the scientific backbone of AAES-OS v1.0.
