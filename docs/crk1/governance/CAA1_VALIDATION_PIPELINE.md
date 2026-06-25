# CAA-1 / CXD-1 Governance Validation Pipeline

## Purpose

This pipeline defines how the Governance Layer validates CAA-1 / CXD-1 receipts before accepting continuity propagation claims.

## Pipeline Stages

### Stage 1 — Structural Validation

- Schema compliance (`CAA1ContinuityAssimilationReceipt`)
- Required fields present
- Hash formats valid (64-char lowercase hex)

### Stage 2 — Isolation Validation

- Verify isolation proof
- Cross-check participation logs
- Confirm no contamination

Implementation: `compute_isolation_proof()` in `src/crk1/caa1_assimilation.py`

### Stage 3 — Lineage Validation

- Recompute CRR-1 hash
- Recompute CLG-1 hash
- Compare with `receipt.lineage_used`

### Stage 4 — Metric Validation

- Recompute Q_pre from `pre_trace.json`
- Recompute Q_post from `post_trace.json`
- Recompute ΔA
- Verify ΔA ≥ τA

### Stage 5 — Proof Bundle Validation

- Recompute proof bundle from receipt fields
- Compare with `receipt.proof_bundle`

### Stage 6 — Governance Decision

| Result | Meaning |
|--------|---------|
| **PASS** | Continuity propagated |
| **FAIL** | Continuity not demonstrated |

## Audit Outputs

| File | Description |
|------|-------------|
| `CAA1_validation_report.json` | Stage-by-stage results |
| `governance_decision.json` | Final PASS/FAIL |
| `continuity_propagation_log.json` | Append-only audit log |

## Implementation

```python
from src.crk1.caa1_assimilation import validate_caa1

validate_caa1(receipt)  # raises on failure
```

TypeScript SDK: `validateCAA1()` in `sdk/continuity-sdk/crk1/receipts/caa1.ts`
