# Artifact Governance Model

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Purpose:** Define the shared governance metadata model for major artifacts across the CIS ecosystem, implementation platform, and supporting release docs.

---

## 1. Why this exists

The ecosystem becomes machine-governable only if major artifacts all describe themselves the same way.

This model standardizes the fields each major artifact should carry:

- Document Status
- Version
- Owner / Steward
- Normative or Informative classification
- Parent Specification
- Traceability Links
- CCP / CCR History
- Release History

## 2. Governance rule

Every major artifact should have:

- a normative status
- a named steward
- a stable parent specification
- explicit traceability links
- recorded constitutional change history
- recorded release history

## 3. Classification model

| Classification | Meaning |
|---------------|---------|
| Normative | Defines requirements, principles, conformance, or governance rules |
| Informative | Explains, guides, or operationalizes normative material without redefining it |

## 4. Required fields

| Field | Meaning |
|------|---------|
| Document Status | Lifecycle position such as Draft, Review, Baseline Candidate, Frozen, or Published |
| Version | Stable version identifier for the artifact |
| Owner / Steward | Person, team, or body accountable for the artifact |
| Normative or Informative | Whether the artifact defines requirements or provides guidance |
| Parent Specification | The governing specification that this artifact inherits from |
| Traceability Links | Links to related requirements, tests, evidence, or downstream artifacts |
| CCP / CCR History | Constitutional change request and approval history |
| Release History | Published releases and their milestones |

## 5. Governance lifecycle

Major artifacts should advance through a predictable lifecycle:

`Draft -> Technical Review -> Baseline Candidate -> Constitutional Approval -> Frozen -> Published`

## 6. Self-description rule

Every artifact should be able to answer:

- what it is
- who owns it
- what it inherits from
- what it proves
- how it changed
- what evidence supports it
- what test or review verifies it

## 7. Machine-governable bundle

The machine-readable registry for this model lives in [ARTIFACT_GOVERNANCE_REGISTRY.spec.json](./ARTIFACT_GOVERNANCE_REGISTRY.spec.json).
