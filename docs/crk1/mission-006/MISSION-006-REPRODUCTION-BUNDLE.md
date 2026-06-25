# Mission #006 Full Reproduction Bundle

Everything required for a third-party lab, research group, or engineering team to fully reproduce Mission #006.

## Bundle Contents

### A. Required Artifacts

| Artifact | Location |
|----------|----------|
| CRR-1 (calibration receipt) | Mission #005 output / `fixtures/crk1/` |
| CLG-1 (lineage graph) | `src/crk1/calibration_lineage_graph_clg1.py` |
| Judgment task specification | `physics.fall_time` in `mission_006_calibration_assimilation.py` |
| τA (assimilation threshold) | Default 0.15; see [TA_SPEC.md](../standards/TA_SPEC.md) |
| CPM metric definition | [CPM.md](../metrics/CPM.md) |
| CAA-1 schema | `fixtures/crk1/CAA1_continuity_assimilation_receipt.schema.json` |
| Assimilation harness | `sdk/continuity-sdk/harness/` (Python + TypeScript) |

### B. Required Environment

- Deterministic or controlled randomness
- Version-locked runtime (`pyproject.toml`, `continuity-engine/package.json`)
- Isolation logs
- Steward identity registry

### C. Required Procedures

1. Steward isolation
2. Pre-test
3. Lineage replay
4. Post-test
5. ΔA computation
6. CAA-1 emission
7. Governance validation

### D. Required Outputs

| File | Description |
|------|-------------|
| `CAA1_receipt.json` | Continuity receipt |
| `pre_trace.json` | Pre-assimilation trace |
| `post_trace.json` | Post-assimilation trace |
| `isolation_material.txt` | Steward isolation evidence |
| `validation_report.json` | Proof Layer report |

Example receipt: `fixtures/crk1/sample_caa1_receipt.json`

### E. Reproduction Standard

A Mission #006 claim is valid only if:

- ≥ 3 independent stewards
- ΔA ≥ τA for each
- All receipts validated
- No contamination detected

See [MISSION-006-MULTI-STEWARD-REPLICATION.md](./MISSION-006-MULTI-STEWARD-REPLICATION.md).

## Run

```bash
python -m pytest tests/mission006/ -v
```

```bash
cd sdk/continuity-sdk && npm install && npm test
```
