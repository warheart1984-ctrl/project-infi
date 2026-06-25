# Nova Control Tower — Distributed Constitutional Consensus Protocol

**Version:** 1.0  
**Purpose:** Distributed consensus for multi-agent Nova clusters.

---

## 1. Consensus Goals

- Cross-agent constitutional, continuity, and ledger coherence
- Cross-agent PIT-band and dLAP alignment
- Drift detection and correction
- Fail-closed behavior

---

## 2. Consensus Model

Hybrid **Raft-like** + **CRDT-like**:

| Raft-like | CRDT-like |
|-----------|-----------|
| Leader election | Conflict-free ledger merges |
| Log replication | Conflict-free continuity merges |
| Majority quorum | Conflict-free PIT merges |
| Heartbeats | Convergence without central lock |

---

## 3. Protocol Overview

### 3.1 Leader Election

Leader coordinates constitutional state and distributes PIT/continuity updates.

### 3.2 Log Replication

Receipts, continuity snapshots, and PIT transitions replicated across agents.

### 3.3 Drift Detection

Drift when: ledger mismatch, continuity mismatch, PIT mismatch, invariant mismatch.

### 3.4 Drift Correction

Leader computes canonical state → followers reconcile → CRDT merge → revalidate continuity and ledger.

### 3.5 Fail-Closed

If drift cannot be resolved: cluster halts, operators notified, forensics required.

---

## 4. Guarantees

Strong eventual consistency · Deterministic convergence · Drift detection · Drift correction · Fail-closed safety · Constitutional coherence
