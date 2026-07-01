# RFC-COR-SUITE-1.0

**Constitutional Observability, Validation, Measurement, Analysis, Governance, and Communication Architecture**

| Field | Value |
|-------|-------|
| **Status** | Proposed Standard |
| **Version** | 1.0 |
| **Editors** | Halstead, J. |
| **Category** | Standards Track |

---

## 1. Introduction

This RFC defines the COR Suite, a constitutional architecture for evidence-first software governance.

Version 1.0 introduces a stable six-layer model:

1. **Canonical Layer** (CAR-1.0)
2. **Validation Layer** (CAV-1.0)
3. **Measurement Layer** (COR-1.0, CSR-1.0, DRA-1.0)
4. **Analysis Layer** (Proof Analysis)
5. **Governance Layer** (Steward Council)
6. **Communication Layer** (Public Documentation)

This layering ensures that:

- canonical truth is explicitly declared
- validation verifies integrity
- measurement reports state
- analysis explains consequences
- governance makes decisions
- communication reflects results

The repository never declares itself correct. Correctness is demonstrated through reproducible evidence.

---

## 2. Terminology

**Canonical Artifact** — any requirement, specification, implementation, verification, evidence, schema, or governance receipt registered in CAR-1.0.

**CAR-1.0** — Canonical Artifact Registry.

**CAV-1.0** — Canonical Validation.

**Measurement Artifacts** — COR-1.0, CSR-1.0, DRA-1.0.

**Proof Analysis** — reasoning layer producing derived claims.

**Steward Council** — governance authority.

**Blocking Finding** — must be resolved before release.

**Advisory Finding** — non-blocking but relevant to governance.

---

## 3. Architectural Overview

The COR Suite defines six strictly separated layers:

1. Canonical Layer (CAR-1.0)
2. Validation Layer (CAV-1.0)
3. Measurement Layer (COR-1.0, CSR-1.0, DRA-1.0)
4. Analysis Layer (Proof Analysis)
5. Governance Layer (Steward Council)
6. Communication Layer (Public Documentation)

Each layer consumes the outputs of the layer below and **MUST NOT** assume responsibilities of any other layer.

---

## 4. Canonical Layer — CAR-1.0 (Normative)

### 4.1 Purpose

CAR-1.0 defines the authoritative inventory of all canonical artifacts.

### 4.2 Requirements

CAR-1.0 **MUST**:

- register every canonical artifact explicitly
- assign each artifact a stable ID, namespace, kind, version, status, authority, schemaRef, path, and hash
- record lifecycle timestamps (created, updated, deprecated, retired)
- record supersession and related-artifact links
- serve as the single source of truth for all downstream layers

### 4.3 Prohibitions

CAR-1.0 **MUST NOT**:

- infer canonical artifacts from repository scans
- omit any artifact required by the constitutional specification
- contain duplicate IDs or conflicting lifecycle states

**Schema:** [car-1.0.schema.json](./car-1.0.schema.json) · **Contract:** [CAR-1.0-Registry.md](./CAR-1.0-Registry.md)

---

## 5. Validation Layer — CAV-1.0 (Normative)

### 5.1 Purpose

CAV-1.0 verifies the integrity of canonical state.

### 5.2 Requirements

CAV-1.0 **MUST**:

- validate CAR-1.0 against its schema
- verify that each artifact exists at its registered path
- verify that each artifact's hash matches its content
- verify that required canonical artifacts are present
- verify that provenance chains are complete and unbroken

### 5.3 Findings Classification

#### Blocking Findings

These **MUST** be resolved before release:

- invalid canonical artifacts
- broken provenance chains
- missing required canonical artifacts
- schema violations

#### Advisory Findings

These **MAY** be resolved post-release:

- research claims
- high dependency-risk nodes
- non-critical verification gaps
- deprecated authorities with valid successors

### 5.4 Prohibitions

CAV-1.0 **MUST NOT**:

- perform measurement
- perform analysis
- issue governance decisions

**Schema:** [cav-validation.schema.json](./cav-validation.schema.json) · **Contract:** [CAV-1.0-Validation.md](./CAV-1.0-Validation.md)

---

## 6. Measurement Layer — COR-1.0, CSR-1.0, DRA-1.0 (Normative)

### 6.1 Purpose

The measurement layer computes descriptive constitutional state from canonical artifacts.

### 6.2 Inputs

- CAR-1.0
- CAV-1.0 findings

### 6.3 Components

#### COR-1.0 — Constitutional Observability

**MUST** produce:

- requirements
- specifications
- implementations
- verifications
- evidence
- maturity levels
- structural integrity exceptions

#### CSR-1.0 — Constitutional Stewardship Report

**MUST** measure:

- steward participation
- governance activity
- decision coverage

#### DRA-1.0 — Dependency-Risk Assessment

**MUST** measure:

- dependency depth
- risk concentration
- readiness indicators

### 6.4 Prohibitions

Measurement **MUST NOT**:

- infer missing artifacts
- interpret findings as decisions
- modify canonical state

**Contract:** See skillzmcgee `spec/COR-1.0-Contract.md` · **Schema:** [cor-state-vector.schema.json](./cor-state-vector.schema.json)

---

## 7. Analysis Layer — Proof Analysis (Normative)

### 7.1 Purpose

Proof Analysis explains the consequences of canonical and measured state.

### 7.2 Requirements

Proof Analysis **MUST**:

- compute dependency maps
- detect regressions
- perform counterfactual analysis
- produce derivation traces

### 7.3 Prohibitions

Proof Analysis **MUST NOT**:

- modify CAR-1.0
- modify measurement outputs
- issue governance decisions

---

## 8. Governance Layer — Steward Council (Normative)

### 8.1 Purpose

The Steward Council evaluates validated and measured state against published criteria.

### 8.2 Inputs

- CAV-1.0 findings
- COR-1.0, CSR-1.0, DRA-1.0
- Proof Analysis
- constitutional invariants
- release criteria

### 8.3 Decisions

Governance **MAY**:

- approve
- reject
- require fixes
- escalate
- freeze
- retire

### 8.4 Governance Receipts

Governance receipts **MUST** include:

- decision ID
- steward identity
- timestamp
- rationale
- evidence references
- invariants enforced
- signature

Receipts **MUST** be registered in CAR-1.0 as canonical artifacts.

### 8.5 Prohibitions

Governance **MUST NOT**:

- modify canonical artifacts directly
- override validation failures
- reinterpret measurement outputs

**Schema:** [governance-receipt.schema.json](./governance-receipt.schema.json)

---

## 9. Communication Layer — Public Documentation (Non-Normative)

### 9.1 Purpose

To generate public-facing documentation derived from validated, measured, and governed state.

### 9.2 Requirements

Communication **MUST**:

- reflect canonical, validated, measured, and governed state
- remain strictly derivative

Communication **MUST NOT**:

- introduce new canonical artifacts
- override governance decisions

---

## 10. Security Considerations

- CAR-1.0 **MUST** be tamper-evident
- CAV-1.0 **MUST** detect unauthorized modifications
- Governance receipts **MUST** be signed
- All measurement artifacts **MUST** be reproducible

---

## 11. Reproducibility Considerations

- All canonical artifacts **MUST** be reproducible
- All validation **MUST** be independently verifiable
- All measurement **MUST** be deterministic
- All analysis **MUST** be traceable
- All governance decisions **MUST** reference reproducible evidence

---

## 12. Change Control and Stewardship

- Changes to CAR-1.0 **MUST** be governed
- Amendments to this RFC **MUST** follow the Steward Council process
- Deprecations **MUST** include supersession links
- Retirements **MUST** preserve historical lineage

---

## 13. Appendix A: Rationale

The introduction of CAR-1.0 and CAV-1.0 formalizes the separation between:

- canonical truth
- validation of truth
- measurement of state
- analysis of consequences
- governance decisions
- public communication

This ensures founder independence and long-term reproducibility.

---

## 14. Appendix B: Non-Goals

This RFC does **NOT**:

- define programming languages
- define build systems
- define governance policies
- define human review processes
- define correctness criteria

It defines how correctness is evidenced, not what correctness means.

---

## Reference implementation

This repository: `cor-suite/` — `npm run pipeline`

Cockpit (read-only): skillzmcgee `cor-client/` and Nova Studio `/nova/studio/cor`

---

**END OF RFC-COR-SUITE-1.0**
