# CRK-2 → CRK-3 Evolution Roadmap

**Goal:** Move from deterministic, drift-aware, distributed CRK-2 to self-describing, meta-constitutional CRK-3.

---

## Phase 1 — CRK-2 Hardening

- Finalize dLAP semantics
- Prove replay determinism (CRP test suite)
- Harden MACC + Control Tower consensus
- Stabilize ConstraintObject semantics

---

## Phase 2 — Meta-Description Layer

CRK-3 introduces:

- Meta-schema describing constitutional objects
- Self-describing invariant registry
- Meta-continuity layer (continuity of the constitution)

Tasks: define `MetaObject`, `MetaInvariant`, extend ledger for constitutional changes as first-class events.

---

## Phase 3 — Meta-PIT (PIT-6)

PIT-6: meta-constitutional reasoning. May propose amendments but cannot apply them; all amendments require CA-2-like protocol with operator approval.

---

## Phase 4 — CRK-3 Kernel

Implement meta-schema, meta-continuity, PIT-6, constitutional change ledger.

---

## Phase 5 — CRK-2 → CRK-3 Migration

Export CRK-2 state → wrap in CRK-3 meta-schema → rebuild anchors → validate replay and drift detection.

---

## Phase 6 — CRK-3 Stabilization

Fuzz meta-layer · multi-agent drift simulations · lock CRK-3 as canonical kernel.
