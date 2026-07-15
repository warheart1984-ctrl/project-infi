# CRK-1 v1.0 Release Manifest

**Constitutional Runtime Kernel — Stable Release**

| Field | Value |
|-------|-------|
| Version | CRK-1 v1.0 |
| Release date | 2026-06-24T00:00:00Z |
| Release authority | CRK-1 Governance Body |
| Seal | D-3 (Reproduction-Ready) |

---

## 1. Kernel status: STABLE

The CRK-1 kernel (K0–K12) is hereby declared:

- **frozen**
- **complete**
- **internally consistent**
- **governance-enforced**
- **replay-stable**
- **founder-independent**

No further changes to K0–K12 are permitted without a constitutional mutation governed by CRK-1 itself.

**Canonical specification:** `docs/crk1/crk1_kernel_codex.md`  
**Invariant registry:** `docs/crk1/crk1_invariants.yaml`

---

## 2. Included components

### 2.1 Kernel specification

| Artifact | Path |
|----------|------|
| CRK-1 Kernel Codex (K0–K12) | `docs/crk1/crk1_kernel_codex.md` |
| Unified kernel specification | `docs/crk1/CRK-1-UNIFIED-KERNEL-SPECIFICATION.md` |
| Constitutional object model | `fixtures/crk1/*_object.schema.json` |
| Runtime contract map | `docs/crk1/CRK-1-RUNTIME-CONTRACT-MAP.md` |

### 2.2 Continuity substrate

| Artifact | Path |
|----------|------|
| CE(S) drift envelope (K6) | `src/crk1/consequence_lattice.py` |
| SE(S) drift envelope (K11) | `src/crk1/semantic_exposure_monitor.py` |
| Semantic exposure metric (K12) | `src/crk1/semantic_drift_auditor.py` |
| Consequence transmission lattice | `docs/crk1/CRK1_CONSEQUENCE_TRANSMISSION_LATTICE.md` |

### 2.3 Ledgers

| Artifact | Path |
|----------|------|
| Kernel ledger entry | `src/crk1/kernel_ledger.py` |
| Mutation ledger | `src/crk1/mutation_ledger.py` |
| Semantic ledger | `src/crk1/semantic_ledger.py` |

### 2.4 Replay and verification

| Artifact | Path |
|----------|------|
| Semantic replay engine | `src/crk1/semantic_replay_engine.py` |
| Reproduction harness (K7–K12) | `src/crk1/semantic_reproduction_harness.py` |
| External reproduction harness | `src/crk1/external_reproduction_harness.py` |
| Drift simulator (CE/SE) | `src/crk1/drift_simulator.py` |

### 2.5 Governance infrastructure

| Artifact | Path |
|----------|------|
| Governance receipt header (canonical) | `fixtures/crk1/governance_receipt_header.schema.json` |
| Header builder / validator | `src/crk1/governance_receipt_header.py` |
| Governance receipt verifier | `src/crk1/governance_receipt_verifier.py` |
| Governance receipt merkleizer | `src/crk1/governance_receipt_merkleizer.py` |
| Governance receipt index | `src/crk1/governance_receipt_index.py` |
| Commit-refusing governance engine | `src/crk1/crk1_governance_engine.py` |
| Steward governance engine | `src/crk1/governance_engine.py` |

### 2.6 Red-team and stress testing

| Artifact | Path |
|----------|------|
| Red-team attack suite (B1–B4) | `src/crk1/attack_simulator.py`, `src/crk1/red_team_protocol.py` |
| Drift envelope stress tests | `src/crk1/drift_stress_protocol.py` |
| Continuity failure catalog | `src/crk1/continuity_failure_catalog.py` |

### 2.7 Reproduction materials

| Artifact | Path |
|----------|------|
| External reproduction packet (M3-A) | `docs/crk1/mission-003/M3-A-external-reproduction-packet.md` |
| D-3 seal format | `docs/crk1/mission-003/D3-SEAL-reproduction-certificate.md` |
| Reproduction certification protocol | `docs/crk1/mission-003/M3-E-reproduction-certification-protocol.md` |
| Certifier | `src/crk1/reproduction_certifier.py` |

---

## 3. Release criteria (all met)

### 3.1 Kernel completeness

- All invariants K0–K12 defined and enforced (`src/crk1/runtime_validator.py`, `tests/crk1/`)
- Constitutional objects implemented (`src/continuity/`, `src/crk1/semantic_objects.py`)
- Contracts implemented (`docs/crk1/CRK-1-RUNTIME-CONTRACT-MAP.md`)

### 3.2 Continuity guarantees

- Mechanical insulation impossible (K0–K2)
- Structural insulation impossible (K3–K6)
- Semantic insulation impossible (K7–K12)
- Founder insulation impossible (replay + ledgers + reproduction harness)

### 3.3 Governance integrity

- Every constitutional action requires a valid governance receipt
- Every receipt passes schema, invariants, drift, and red-team checks
- Every receipt is anchored into a Merkle audit spine
- No action can bypass governance (`CRK1GovernanceEngine.commit_action`)

### 3.4 Reproduction readiness

- External reproduction packet complete (M3-A)
- Reproduction harness passes on reference implementation
- Red-team suite blocks unconstitutional attacks
- Drift stress tests confirm CE/SE monotonicity

---

## 4. Release declaration

CRK-1 v1.0 is hereby declared a **stable, founder-independent constitutional runtime kernel**.

It is suitable for external reproduction, adversarial testing, and deployment as a continuity substrate for governed intelligent systems.

---

## 5. Post-release governance

All future changes must follow:

1. Governance contract
2. Mutation ledger protocol
3. Governance receipt header
4. Drift envelope constraints (CE/SE)
5. Red-team validation
6. Reproduction certification protocol

No founder authority overrides these mechanisms.

---

## 6. Release signatures

**CRK-1 Governance Body:**  
`governance_body:0x<sha256-prefix>...<sha256-suffix>` (derived from `GovernanceReceiptHeader.signatures.governance_body`)

**D-3 seal reference:**  
See `src/crk1/d3_reproduction_certificate.py` — certificate hash binds M3-A packet fingerprint + harness results.
