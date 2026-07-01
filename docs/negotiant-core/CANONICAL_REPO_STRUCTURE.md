# Canonical Negotiant Core Repository Structure

This document defines the proposed standalone repository layout for Negotiant Core. It is a structural target, not evidence that the implementation already exists.

```text
negotiant-core/
  README.md
  package.json
  pyproject.toml
  spec/
    negotiant-core-v1.1.md
    constitutional-principles.md
    invariants.md
    versioning-contract.md
    governance-model.md
    evidence-claim-discipline.md
    theta-canon-invariants.md
    cockpit-provenance.md
    governance-validation-layer.md
    paradox-resolution-spec.md
    faction-input-translator.md
  runtime/
    core/
      capacity-relation.ts
      constraint-engine.ts
      continuation-engine.ts
      core-tick.ts
      cosmos-state.ts
    rules/
      versioned-rule-tables/
      paradox-resolution-tables/
      propagation-rules/
    fit/
      translator.ts
      rule-table.ts
      translation-receipt.ts
    grvl/
      validator.ts
      signature.ts
  ledger/
    schemas/
      governance-receipt.schema.json
      capacity-evaluation-receipt.schema.json
      paradox-receipt.schema.json
      fit-translation-receipt.schema.json
      cockpit-indicator.schema.json
      zoneTick.json
      factionTick.json
      governanceTick.json
    validation/
      shape-validator.ts
      normative-validator.ts
      provenance-validator.ts
    replay/
      replay-engine.ts
    verifier/
      independent-verifier.ts
      replication-report-validator.ts
  faces/
    language/
    rpg/
    governance/
    scripture/
    cosmology/
  cockpit/
    indicators/
      capacity-indicator.md
      capacity-utilization-indicator.md
      capacity-risk-band-indicator.md
      constraint-indicator.md
      paradox-indicator.md
      verification-indicator.md
    provenance/
      metadata.ts
      transformation-specs/
    reference/
      indicator-computation.ts
    verifier/
      indicator-verifier.ts
  governance/
    receipt-schemas/
    validation-layer/
    authorization-chains/
    challenge-protocol.md
  evidence/
    cts/
    replay-logs/
    verification-reports/
    replication-reports/
    fixtures/
  research/
    hypotheses.md
    experiments/
      multi-face-arbitration.md
      paradox-topology.md
  docs/
    whitepaper/
      negotiant-core-v1.1.md
    diagrams/
      epistemic-layers.mmd
      provenance-flow.mmd
      verification-boundary.mmd
    contribution-taxonomy.md
    research-hypotheses.md
```

## Ownership Boundaries

| Directory | Responsibility |
|-----------|----------------|
| `spec/` | Normative language and conformance obligations |
| `runtime/` | Reference implementation and versioned rule execution |
| `ledger/` | Receipts, replay, validation, and independent verification |
| `faces/` | Domain-specific interpretive surfaces over the same substrate |
| `cockpit/` | Indicator definitions, provenance metadata, reference computation, independent verification |
| `governance/` | Receipt validation, authorization chains, and challenge protocol |
| `evidence/` | CTS, replay logs, verification reports, and fixtures |
| `docs/` | Whitepaper, diagrams, contribution taxonomy, and research hypotheses |

## First Implementation Slice

The smallest useful implementation slice is:

1. `spec/negotiant-core-v1.1.md`
2. `spec/theta-canon-invariants.md`
3. `runtime/core/capacity-relation.ts`
4. `runtime/core/core-tick.ts`
5. `ledger/schemas/capacity-evaluation-receipt.schema.json`
6. `ledger/validation/shape-validator.ts`
7. `ledger/replay/replay-engine.ts`
8. `cockpit/indicators/capacity-indicator.md`
9. `cockpit/indicators/capacity-utilization-indicator.md`
10. `evidence/cts/capacity-relation.test.ts`

This slice proves the core loop: specify NC-Phi.1, compute continuation capacity, compare it to proposed delta, receipt the decision, replay it, and expose its cockpit provenance.
