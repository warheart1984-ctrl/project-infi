# COR Suite — Consolidated Specification (v1.0)

**Constitutional Architecture for Evidence-First Governance**

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **RFC** | [RFC-COR-Suite-1.0.md](./RFC-COR-Suite-1.0.md) (Proposed Standard) |
| **Status** | Normative |

---

## 0. Purpose

The COR Suite defines the constitutional substrate for evidence-first software governance.

Version 1.0 establishes a stable six-layer architecture:

1. **Canonical Layer** — CAR-1.0
2. **Validation Layer** — CAV-1.0
3. **Measurement Layer** — COR-1.0, CSR-1.0, DRA-1.0
4. **Analysis Layer** — Proof Analysis
5. **Governance Layer** — Steward Council
6. **Communication Layer** — Public Documentation

Each layer has a single responsibility and **MUST NOT** assume the responsibilities of any other layer.

---

## 1. Canonical Layer — CAR-1.0

### 1.1 Purpose

CAR-1.0 defines the authoritative inventory of all canonical artifacts.

### 1.2 Canonical Artifact Types

- Requirements
- Specifications
- Implementations
- Verifications
- Evidence
- Schemas
- Governance receipts
- Registries

### 1.3 CAR-1.0 Requirements

CAR-1.0 **MUST**:

- register every canonical artifact explicitly
- assign each artifact:
  - `id`
  - `namespace`
  - `kind`
  - `version`
  - `status`
  - `authority`
  - `schemaRef`
  - `path`
  - `hash`
  - lifecycle timestamps
  - supersession links
- serve as the single source of truth for all downstream layers

### 1.4 Prohibitions

CAR-1.0 **MUST NOT**:

- infer canonical artifacts from repository scans
- omit required canonical artifacts
- contain duplicate IDs or conflicting lifecycle states

**Schema:** [car-1.0.schema.json](./car-1.0.schema.json) · **Contract:** [CAR-1.0-Registry.md](./CAR-1.0-Registry.md)

---

## 2. Validation Layer — CAV-1.0

### 2.1 Purpose

CAV-1.0 verifies the integrity of canonical state.

### 2.2 Validation Requirements

CAV-1.0 **MUST**:

- validate CAR-1.0 against its schema
- verify artifact existence and hash correctness
- verify required canonical artifacts are present
- verify provenance chains are complete
- classify findings as blocking or advisory

### 2.3 Blocking Findings

- invalid canonical artifacts
- broken provenance chains
- missing required canonical artifacts
- schema violations

### 2.4 Advisory Findings

- research claims
- high dependency-risk nodes
- non-critical verification gaps
- deprecated authorities with valid successors

### 2.5 Prohibitions

CAV-1.0 **MUST NOT**:

- perform measurement
- perform analysis
- issue governance decisions

**Schema:** [cav-validation.schema.json](./cav-validation.schema.json) · **Contract:** [CAV-1.0-Validation.md](./CAV-1.0-Validation.md)

---

## 3. Measurement Layer — COR-1.0, CSR-1.0, DRA-1.0

### 3.1 Purpose

Compute descriptive constitutional state.

### 3.2 Inputs

- CAR-1.0
- CAV-1.0 findings

### 3.3 COR-1.0 Requirements

COR-1.0 **MUST** compute:

- requirements
- specifications
- implementations
- verifications
- evidence
- maturity levels
- structural integrity exceptions

### 3.4 CSR-1.0 Requirements

CSR-1.0 **MUST** compute:

- steward participation
- governance activity
- decision coverage

### 3.5 DRA-1.0 Requirements

DRA-1.0 **MUST** compute:

- dependency depth
- risk concentration
- readiness indicators

### 3.6 Prohibitions

Measurement **MUST NOT**:

- infer missing artifacts
- interpret findings as decisions
- modify canonical state

**Schema:** [cor-state-vector.schema.json](./cor-state-vector.schema.json)

---

## 4. Analysis Layer — Proof Analysis

### 4.1 Purpose

Explain consequences of canonical and measured state.

### 4.2 Requirements

Proof Analysis **MUST**:

- compute dependency maps
- detect regressions
- perform counterfactual analysis
- produce derivation traces

### 4.3 Prohibitions

Proof Analysis **MUST NOT**:

- modify CAR-1.0
- modify measurement outputs
- issue governance decisions

---

## 5. Governance Layer — Steward Council

### 5.1 Purpose

Evaluate validated and measured state against published criteria.

### 5.2 Inputs

- CAV-1.0 findings
- COR-1.0, CSR-1.0, DRA-1.0
- Proof Analysis
- constitutional invariants
- release criteria

### 5.3 Decisions

Governance **MAY**:

- approve
- reject
- require fixes
- escalate
- freeze
- retire

### 5.4 Governance Receipts

Receipts **MUST** include:

- decision ID
- steward identity
- timestamp
- rationale
- evidence references
- invariants enforced
- signature

Receipts **MUST** be registered in CAR-1.0.

**Release criteria:** [../governance/release-criteria/v1.0.md](../governance/release-criteria/v1.0.md)

---

## 6. Communication Layer — Public Documentation

### 6.1 Purpose

Generate public-facing documentation derived from validated, measured, and governed state.

### 6.2 Requirements

Communication **MUST**:

- reflect canonical, validated, measured, and governed state
- remain strictly derivative

---

**END OF CONSOLIDATED SPEC**
