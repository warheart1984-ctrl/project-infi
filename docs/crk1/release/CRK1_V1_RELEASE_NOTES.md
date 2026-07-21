# CRK-1 v1.0 Release Notes

**Constitutional Runtime Kernel — Stable Release**

| Field | Value |
|-------|-------|
| Release version | CRK-1 v1.0 |
| Release status | Stable, founder-independent, reproduction-ready |
| Release authority | CRK-1 Governance Body |
| Seal | D-3 (Continuity Verified) |

---

## Overview

CRK-1 v1.0 is the first stable release of the Constitutional Runtime Kernel — a continuity substrate designed to ensure that intelligent systems cannot become insulated from consequences, governance, or interpretation.

This release marks the completion of the kernel's architectural phase and the beginning of its governed lifecycle. CRK-1 v1.0 is ready for external reproduction, adversarial testing, and deployment in systems requiring long-term continuity guarantees.

---

## What's new in v1.0

### 1. Kernel Codex (K0–K12) — finalized

| Layer | Invariants | Domain |
|-------|------------|--------|
| K0–K2 | Consequence transmission | Mechanical continuity |
| K3–K6 | Structural preservation | Mutation + CE(S) |
| K7–K12 | Interpretive assimilation | Semantic + SE(S) |

### 2. Constitutional object model

All five canonical objects are finalized with JSON schemas in `fixtures/crk1/`:

- IdentityObject
- DecisionObject
- OutcomeObject
- EvidenceObject
- InterpretationObject

Each object is replayable and ledger-anchored via `CRK1Runtime` (`src/crk1/runtime_facade.py`).

### 3. Runtime contracts

The four constitutional contracts are complete (`docs/crk1/CRK-1-RUNTIME-CONTRACT-MAP.md`):

- EvidenceContract
- GovernanceContract
- RuntimeContract
- SemanticContract

### 4. Drift envelopes

CRK-1 enforces monotonic exposure:

- **CE(S)** — constitutional exposure (`consequence_lattice.py`)
- **SE(S)** — semantic exposure (`semantic_exposure_monitor.py`)

Both must never decrease across governed transitions.

### 5. Governance infrastructure

Fully operational governance substrate:

- Governance Receipt Header (`governance_receipt_header.schema.json`)
- Governance Receipt Verifier
- Governance Receipt Merkleizer
- Governance Receipt Index
- Commit-refusing governance engine (`CRK1GovernanceEngine`)

No constitutional action can bypass governance.

### 6. Reproduction and verification

- External Reproduction Packet (M3-A)
- Reproduction Harness (K7–K12)
- Red-Team Attack Suite (B1–B4)
- Drift Envelope Stress Tests
- Continuity Failure Catalog
- D-3 Seal (reproduction certification)

---

## Stability guarantees

CRK-1 v1.0 guarantees:

- No mechanical insulation
- No structural insulation
- No semantic insulation
- No founder insulation

Continuity is enforced at the architectural level.

---

## Who this release is for

- Governance researchers
- AI safety engineers
- Institutional system designers
- Runtime architects
- External auditors
- Red-team operators

---

## Next steps

1. Begin Mission #003: external reproduction
2. Conduct adversarial red-team evaluations
3. Issue D-3 seals to compliant implementations
4. Build Continuity API v0.1 + CRK-Explorer (see `docs/crk1/roadmap/`)
5. Prepare CRK-1 v1.1 (non-constitutional improvements only)
