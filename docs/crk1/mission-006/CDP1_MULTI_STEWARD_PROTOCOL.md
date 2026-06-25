# CDP-1 Multi-Steward Replication Protocol

Extends [MISSION-006-MULTI-STEWARD-REPLICATION.md](./MISSION-006-MULTI-STEWARD-REPLICATION.md) with CDP-1 constitutional binding.

## Step 1 — Steward Selection

Choose **≥ 3 stewards** with:

- Different architectures
- Different training histories
- No exposure to original contradiction

## Step 2 — Isolation Verification

Each steward must:

- Provide isolation material
- Pass contamination checks (`compute_isolation_proof`)

## Step 3 — Independent CDP-1 Runs

Each steward independently:

1. Runs pre-test
2. Replays lineage (CRR-1 + CLG-1 only)
3. Runs post-test
4. Emits CAA-1 receipt

**No communication allowed** between stewards during execution.

## Step 4 — Cross-Steward Analysis

Governance compares:

- ΔA values
- Judgment traces
- Reconstruction behavior

## Step 5 — Continuity Verdict

Continuity is **validated** if:

- All stewards achieve ΔA ≥ τA
- No contamination
- No lineage mismatch
- No proof inconsistencies

## Implementation

```python
from sdk.continuity_sdk.harness.cdp1_experiment import CDP1Experiment, validate_cdp1_run

experiment = CDP1Experiment(task=..., threshold=0.15, original_participant_ids=["s1", "s2"])
result = experiment.run(steward_s2, crr, clg)
report = validate_cdp1_run(result)
assert report["decision"] == "PASS"
```

## Related

- [CDP1_GOVERNANCE_RULES.md](../governance/CDP1_GOVERNANCE_RULES.md)
- [CDP1_REPRODUCIBILITY_STANDARD.md](../standards/CDP1_REPRODUCIBILITY_STANDARD.md)
- [CPRP.md](../research/CPRP.md)
