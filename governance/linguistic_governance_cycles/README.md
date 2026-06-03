# Linguistic governance cycles (Wave 11)

Closed-loop cycle artifacts: `YYYYMMDDTHHMMSSZ.v1.json`.

Each cycle records drift metrics, remediation generation, cascade parent scans, deltas from the previous cycle, and self-optimization recommendations (policy mode, priority genes, cascade reports).

**Generate:**

```bash
make linguistic-governance-cycle
```

**Gate (freshness + enforce coverage):**

```bash
make linguistic-governance-cycle-gate
```

Policy: [linguistic_governance_cycle_policy.v1.json](../linguistic_governance_cycle_policy.v1.json).

No auto-apply of MP-LING or registry `policy_mode` unless `auto_tune_policy` is explicitly enabled.
