# Negotiant Core v1.1 Diff

This document records the canonical change set from Negotiant Core v1.0 to v1.1.

## Section-Level Diff

| Change | Section | Description |
|--------|---------|-------------|
| Added | 1 | Universal Capacity Relation: `Phi(x) = C(x) - M(x)` |
| Added | 2 | Four-way evidence framing |
| Added | 3 | Replayability vs independent verifiability |
| Added | 4 | Contribution taxonomy |
| Added | 5.4 | Invariant NC-Phi.1 - Capacity for Lawful Continuation |
| Added | 5.5 | Concrete `C(S_t)` and `M(S_t)` cosmos functionals |
| Added | 5.6 | `coreTick` capacity gate using `Delta <= Phi` |
| Added | 5.9.1 | Paradox Resolution Specification |
| Added | 8 | Cockpit indicator provenance |
| Added | 9.4.1 | Governance Receipt Validation Layer |
| Split | 10 | Reproducibility guarantees into replayability, independent verifiability, and independent replication |
| Added | 11 | Epistemic layer diagram |
| Added | 12 | Security and epistemic drift resistance |
| Added | 13 | Versioning and evolution model by epistemic role |
| Added | 14.8.1 | Faction Input Translator |
| Added | 15 | Provenance and verification boundary diagrams |
| Modified | Conclusion | Recast as discipline statement |

## Semantic Diff

### New invariants

| Invariant | Meaning |
|-----------|---------|
| NC-Phi.1 - Capacity for Lawful Continuation | `Phi(S_t) = C(S_t) - M(S_t) >= 0`; proposed transition delta must not exceed current continuation capacity |
| Paradox must be receipted | A paradox cannot be silently erased by selecting one side |
| Translation preserves source | FIT must preserve original faction input and unresolved ambiguity |
| Indicators are observational | Cockpit indicators expose evidence and provenance, not ungrounded truth |
| Verification boundaries matter | Replayability and independent verifiability are separate evidence classes |

### New obligations

| Obligation | Applies to |
|------------|------------|
| Assign claim class | All claims |
| Cite normative basis | Specified guarantees |
| Cite artifacts | Empirical claims |
| Emit paradox receipts | Paradox handling |
| Emit translation receipts | FIT |
| Attach provenance metadata | Cockpit indicators |
| Validate receipt shape, normative basis, provenance, replay, and independent verification | Governance receipts |
| Compute `continuation_capacity_t` | `zoneTick` and `coreTick` receipts |
| Compute `proposed_delta_t` | `zoneTick` and `coreTick` receipts |
| Reject transitions where `Delta_t > Phi_t` | `coreTick` |
| Record `epistemic_classification` | `governanceTick` |
| Record `grvl_signature` | `governanceTick` |

### New epistemic categories

1. Architectural objectives
2. Specified guarantees
3. Empirical claims
4. Research hypotheses

Attachment terminology also maps these into normative specification, reference implementation, evidence, and research hypotheses.

### New evidence tiers

1. Replayability
2. Independent Verifiability
3. Independent Replication

### New validation layers

| Layer | Purpose |
|-------|---------|
| NC-Phi.1 Capacity Gate | Rejects attempted state changes that exceed lawful continuation capacity |
| Governance Receipt Validation Layer | Validates receipts before verification promotion |
| Cockpit Indicator Provenance Layer | Binds displayed indicators to artifacts and verifier status |
| Faction Input Translator | Converts faction-specific input into canonical governance objects |
| Paradox Resolution Layer | Detects, classifies, bounds, resolves, or defers paradox |

## Governance Diff

| Now requires receipts | Receipt type |
|-----------------------|--------------|
| Paradox detection | `paradox.detected` |
| Paradox classification | `paradox.classified` |
| Paradox boundary definition | `paradox.bounded` |
| Paradox resolution or deferral | `paradox.resolved` or `paradox.deferred` |
| Faction translation | `fit.translation` |
| Governance receipt validation | `governance.receipt.validated` |
| Cockpit indicator verification update | `cockpit.indicator.verified` |
| Capacity gate rejection | `constitutional.error.capacity_exceeded` |
| zoneTick or coreTick capacity evaluation | `capacity.evaluated` |
| Change to epistemic classification rules | `governance.epistemic_classification.changed` |
| Change to NC-Phi.1, GRVL, or FIT | `governance.core_obligation.changed` |

| Now requires validation | Validation basis |
|------------------------|------------------|
| Governance receipts | Schema, normative basis, provenance, replay, independent verifier |
| Cockpit indicators | Normative definition, reference implementation, independent verifier |
| NC-Phi.1 capacity gate | `Phi_t`, `Delta_t`, and `Delta_t <= Phi_t` |
| Governance receipts | GRVL signature and epistemic classification |
| Faction decisions | FIT translation receipt |
| Empirical claims | Artifact citation and replay or verification status |
| Specified guarantees | Normative clause and CTS or conformance evidence |

| Now requires provenance | Provenance fields |
|-------------------------|-------------------|
| Cockpit indicators | Source artifacts, transformation specification, implementation version, verification status |
| FIT outputs | Source input, translator version, rule table, unresolved ambiguity |
| Paradox outcomes | Inputs, type, boundary, rule version, residue |
| Capacity decisions | Mass state, constraint basis, `continuation_capacity_t`, `proposed_delta_t`, capacity check result, implementation version |

## Reproducibility Diff

| Category | Version 1.0 tendency | Version 1.1 requirement |
|----------|----------------------|-------------------------|
| Replay-obligated | Reproducibility sometimes stated broadly | Reference implementation replay must be recorded separately |
| Independently verifiable | Often grouped with replay | Separate implementation boundary required |
| Provenance-tracked | Implied by evidence language | Explicit metadata required for each cockpit indicator |
| Claim status | Claims could be bundled together | Claim class must be declared |
| Capacity gate | Continuation could remain conceptual | `zoneTick` and `coreTick` record `Phi_t`, `Delta_t`, and `capacity_check_passed` |
| Replication | Often merged with verification | Independent Replication is a separate tier |

## Version History Entry

Version 1.1 adds epistemic claim discipline, separates replayability from independent verifiability and independent replication, adds NC-Phi.1 as a quantitative continuation-capacity invariant, adds cockpit indicator provenance, introduces the Governance Receipt Validation Layer, adds FIT, adds epistemic drift resistance, adds role-aware versioning, adds the Paradox Resolution Specification, and reframes the conclusion as a discipline statement.
