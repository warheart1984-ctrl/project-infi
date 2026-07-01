## 6.4 Epistemic Receipts

Epistemic receipts extend lineage receipts with correctness‑oriented metrics.

### Components

1. **Lineage Record**
   - input/output hashes
   - timestamps
   - identity
   - power/thermal context

2. **Epistemic Metrics**
   - uncertainty estimates
   - deviation from baseline
   - cross‑model consistency
   - anomaly scores

3. **Interpretation Set**
   - frames used
   - weights
   - prediction bindings

4. **Correctness Signals**
   - self‑consistency
   - tool‑consistency
   - historical consistency

### Epistemic Faults

| Fault | Severity | Trigger |
|--------|----------|----------|
| EPI_DRIFT | Medium | Behavioral drift |
| EPI_UNCERTAINTY_SPIKE | Medium | Uncertainty exceeds threshold |
| EPI_CONSISTENCY_FAILURE | High | Cross‑checks fail |

---
