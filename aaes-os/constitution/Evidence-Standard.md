# Evidence & Traceability Standard

**Version:** 1.0
**Status:** Foundational
**Date:** June 25, 2026

## Purpose

Ensure every architectural, cognitive, or governance decision is backed by verifiable evidence.

## Foundational Rule

> **Governance should determine how changes are evaluated, but evidence should determine whether changes are adopted.**

Evidence is the adoption authority. Governance structures how evidence is gathered, reviewed, and linked — it is not a substitute for evidence.

## Evidence Types

- empirical data
- stress tests
- invariants
- receipts
- ADRs
- simulations
- historical patterns

## Traceability Chain

```
Principle → Requirement → Specification → ADR → Implementation → CTS Test → Evidence → Receipt
```

## Evidence Storage

- All evidence stored in Artifact Registry
- Immutable, checksummed, versioned

## Reproducibility

- Every decision must be replayable
- Every evaluation must be deterministic

## Adoption Criteria

A change may be adopted only when:

1. Governance evaluation is complete (required reviewers, ADR, registry updates, CTS gates).
2. Linked evidence artifacts exist and support the decision.
3. Evidence level meets the bar for the change class (see `EVIDENCE_LEDGER.md` for v1.0 levels).
4. Contradicting or insufficient evidence blocks adoption regardless of consensus or urgency.
