# Continuity OS Threat Model (v0.1)

First formal threat model for Continuity OS — adversarial, structural, and epistemic threats.

## Threat Class 1 — Preservation Attacks

### T1.1 — GRR-1 Tampering

**Goal:** Rewrite reasoning history  
**Mitigation:** Hash receipts, append-only ledger

### T1.2 — CRR-1 Corruption

**Goal:** Falsify calibration events  
**Mitigation:** Proof Layer P₃, lineage cross-checks

### T1.3 — CLG-1 Breakage

**Goal:** Disconnect calibration lineage  
**Mitigation:** Merkle lineage, orphan detection

## Threat Class 2 — Assimilation Attacks

### T2.1 — Fake Isolation

**Goal:** Steward pretends to be independent  
**Mitigation:** Isolation proofs, participation logs  
**Red-team:** `sdk/continuity-sdk/experiments/failure/assimilation_redteam/forged_isolation.test.ts`

### T2.2 — Threshold Gaming

**Goal:** Set τA artificially low  
**Mitigation:** Governance-enforced minimum τA

### T2.3 — ΔA Fabrication

**Goal:** Fake improvement  
**Mitigation:** Recompute Q_pre/Q_post from raw traces  
**Red-team:** `delta_mismatch.test.ts`

## Threat Class 3 — Governance Attacks

### T3.1 — Proof Bundle Forgery

**Goal:** Fake CAA-1 validity  
**Mitigation:** Proof Layer recomputation (`validateCAA1`)

### T3.2 — Invariant Bypass

**Goal:** Circumvent CRC-1 through CRC-7  
**Mitigation:** CRK-1 veto logic

## Threat Class 4 — Epistemic Attacks

### T4.1 — Contradiction Class Mismatch

**Goal:** Use a different task to fake assimilation  
**Mitigation:** Task-class binding in mission manifest

### T4.2 — Steward Contamination

**Goal:** Stewards share information  
**Mitigation:** Isolation audits, cross-steward entropy checks

## Threat Class 5 — Systemic Attacks

### T5.1 — Lineage Collapse

**Goal:** Remove or reorder calibration history  
**Mitigation:** CLG-1 structural invariants  
**Red-team:** `lineage_tampering.test.ts`

### T5.2 — Continuity Inflation

**Goal:** Claim continuity without propagation  
**Mitigation:** Multi-steward replication requirement (≥ 3 stewards)
