# AAES-OS v1.0 — Release Manager's Checklist

Ensures v1.0 ships only when every deliverable is complete, every release gate is satisfied, and every specified guarantee or empirical claim is backed by evidence. Architectural objectives and research hypotheses must remain explicitly labeled.

---

## 1. Deliverables Complete

- [ ] CAS 1.0 Spec
- [ ] CAS 1.0 Reference Implementation
- [ ] CRK-1 Deterministic Runtime
- [ ] CTS (Conformance Test Suite)
- [ ] CEP (Continuity Experimental Platform)
- [ ] CDP-1 Benchmark
- [ ] SDK
- [ ] Documentation (Spec, Runtime, Governance, Dev Guide)

---

## 2. Release Gates Satisfied

- [ ] CAS 1.0: Independent implementation passes CTS
- [ ] CRK-1: Determinism verified across repeated runs
- [ ] CRK-1: Governance tests pass
- [ ] CTS: All tests pass in CI
- [ ] CEP: CDP-1 runs end-to-end
- [ ] CDP-1: Independent replication complete
- [ ] Documentation matches implementation
- [ ] SDK integration tests pass

---

## 3. Evidence Ledger Updated

- [ ] Each claim has a claim class
- [ ] Specified guarantees and empirical claims have supporting artifacts
- [ ] Specified guarantees and empirical claims have tests, benchmarks, replay validation, or reproducibility artifacts
- [ ] Research hypotheses remain explicitly labeled
- [ ] Replayability and independent verifiability are tracked separately
- [ ] Evidence levels updated
- [ ] Replication status updated
- [ ] Notes added for any gaps

---

## 4. Open Risks Reviewed

- [ ] Implementation risks resolved or mitigated
- [ ] Documentation risks resolved
- [ ] Reproducibility risks resolved
- [ ] Performance risks evaluated
- [ ] Governance risks reviewed

---

## 5. Final Governance Review

- [ ] No architectural drift
- [ ] No new invariants added
- [ ] No new objects added
- [ ] No new governance surfaces added
- [ ] All changes documented
- [ ] Version 2.0 backlog updated

---

## 6. Release Approval

- [ ] Release Manager approval
- [ ] Governance Council approval
- [ ] Public artifacts published
- [ ] Zenodo DOI minted
- [ ] Release notes finalized

---

> **If any box is unchecked, Version 1.0 is not ready.**
