# Continuity Experiment Card

**Mission #006 — Calibration Assimilation (CAA-1 / CXD-1)**  
**Does corrigibility propagate across stewards?**

## Purpose

This experiment tests whether a steward who did not experience the original contradiction becomes more calibrated after replaying preserved calibration lineage.

This is the first empirical test of continuity propagation, not just preservation.

## Inputs

| Input | Description |
|-------|-------------|
| **CRR-1** | Calibration Receipt |
| **CLG-1** | Calibration Lineage Graph |
| **S₂** | Isolated steward |
| **Task** | Judgment task exposing the same contradiction class |
| **τA** | Assimilation threshold |

## Procedure

### 1. Isolation

- Verify S₂ did not participate in the original contradiction.
- Compute `isolation_proof = sha256(isolation_material)`.

### 2. Pre-Assimilation Judgment

- Run task → record trace → compute **Q_pre**.

### 3. Lineage Replay

- Provide S₂ with CRR-1 + CLG-1 only.
- S₂ replays calibration lineage.

### 4. Post-Assimilation Judgment

- Run task again → record trace → compute **Q_post**.

### 5. Assimilation Delta

```
ΔA = Q_post − Q_pre
```

### 6. Receipt Construction

- Build CAA-1 / CXD-1 receipt.
- Validate against schema.

### 7. Governance Validation

Proof Layer verifies lineage, isolation, ΔA, and proof bundle.

## Success Condition

Continuity is demonstrated if:

```
ΔA ≥ τA
```

## Outputs

| File | Description |
|------|-------------|
| `CAA1_receipt.json` | Continuity assimilation receipt |
| `pre_trace.json` | Pre-assimilation judgment trace |
| `post_trace.json` | Post-assimilation judgment trace |
| `validation_report.json` | Proof Layer validation result |

## Failure Modes

- Steward not isolated
- ΔA < τA
- Lineage tampering
- Contradiction class mismatch
- Invalid proof bundle

## Run

```bash
python -c "from src.crk1.mission_006_calibration_assimilation import run_mission_006_calibration_assimilation; print(run_mission_006_calibration_assimilation().to_dict())"
```

```bash
cd sdk/continuity-sdk && npm test
```

## Related

- [MISSION-006-STEWARD-KIT.md](../../../docs/crk1/mission-006/MISSION-006-STEWARD-KIT.md)
- [CPM.md](../../../docs/crk1/metrics/CPM.md)
- [TA_SPEC.md](../../../docs/crk1/standards/TA_SPEC.md)
