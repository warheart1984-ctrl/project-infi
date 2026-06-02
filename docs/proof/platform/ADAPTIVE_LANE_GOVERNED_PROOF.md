# Adaptive Lane Organ — Governed Proof

CISIV stage: **verification**

Claim: Alt-6 fabric minimum carries `operator_lanes` DNA, awakened registry includes
all five platform genes, capability bridge enforces lane resolution, and policy-cap
authority mismatch blocks with auditable reason.

Claim status: **proven** on fabric-minimum gate and pytest.

## Verification

```bash
make alt6-governed-gate
python -m pytest tests/test_adaptive_lane_organ.py tests/test_alt6_governed_eligibility.py tests/test_adaptive_lane_bridge.py -q
```

| Claim | Label |
|-------|-------|
| Fabric minimum genes carry operator_lanes | proven |
| Awakened registry includes all five fabric genes | proven |
| authority_lane aligns with operator profile | proven |
| Policy-cap block on authority lane mismatch | proven |
| Capability bridge consults lane resolution on execute | proven |
| Tier 5 health reports adaptive_lanes_awakened | proven |

- claim_label: proven
- override_command: make alt6-governed-gate
