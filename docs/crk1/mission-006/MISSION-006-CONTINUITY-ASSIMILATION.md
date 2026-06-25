# Mission #006 — Continuity Demonstration via Calibration Assimilation

**Seal:** CAA-1 / CXD-1  
**Status:** Empirical (first mission with empirical success criteria)

## Preamble

Missions #003–#005 established evidence of reconstruction, preservation, and architectural coherence.

Mission #006 is the first mission whose success criteria are **empirical**, not structural. It asks:

> Can a steward who never experienced the original contradiction become more calibrated through preserved lineage alone?

If yes, continuity has propagated across a generational boundary.  
If no, continuity has not yet crossed that boundary.

## Objective

Demonstrate **Calibration Assimilation** using CAA-1 / CXD-1 receipts.

## Success criteria

A steward **S₂**, who did not participate in the original contradiction, must:

1. Reconstruct calibration lineage (CLG-1)
2. Replay calibration event (CRR-1)
3. Perform a judgment task exposing the same contradiction class
4. Emit a CAA-1 / CXD-1 receipt showing:
   - ΔA ≥ τA
   - Valid isolation proof
   - Valid lineage hashes (`crr_hash`, `clg_hash`)
   - Valid proof bundle

Continuity is demonstrated when:

```
ΔA = Q_post − Q_pre ≥ τA
```

Default τA = **0.15** (configurable in `AssimilationContext`).

## Mission steps

| Step | Action |
|------|--------|
| 1 | Select original calibration event — CRR-1 with clear contradiction class (`physics.fall_time`) |
| 2 | Prepare steward S₂ — must not have participated; must provide isolation proof |
| 3 | Pre-assimilation judgment test — measure baseline quality Q_pre |
| 4 | Lineage replay — S₂ reconstructs CLG-1 and replays CRR-1 from Mission #005 |
| 5 | Post-assimilation judgment test — measure updated quality Q_post |
| 6 | Compute ΔA — compare pre/post metrics |
| 7 | Emit CAA-1 / CXD-1 — steward emits continuity assimilation receipt |
| 8 | Governance validation — Proof Layer validates receipt via `validate_caa1()` |

## Constitutional stack

```
                   +------------------------------+
                   |        K-INFINITY            |
                   |  (Corrigibility as Invariant)|
                   +---------------+--------------+
                                   |
                                   v
                     CONTINUITY (Propagation)
                     +------------------------+
                     |   CAA-1 / CXD-1        |
                     | Calibration Assimilation|
                     +-----------+------------+
                                 |
                                 v
                   +----------------------------+
                   |   CLG-1 (Lineage Graph)    |
                   | Calibration Reconstruction |
                   +-------------+--------------+
                                 |
                                 v
                   +----------------------------+
                   |   CRR-1 (Calibration)      |
                   | Calibration Preservation   |
                   +-------------+--------------+
                                 |
                                 v
                   +----------------------------+
                   |   GRR-1 (Reasoning)        |
                   | Provenance Preservation    |
                   +-------------+--------------+
                                 |
                                 v
                   +----------------------------+
                   |        R0 (Genesis)        |
                   +----------------------------+
```

## Implementation

| Artifact | Path |
|----------|------|
| CAA-1 schema | `fixtures/crk1/CAA1_continuity_assimilation_receipt.schema.json` |
| Assimilation runtime | `src/crk1/caa1_assimilation.py` |
| Mission runner | `src/crk1/mission_006_calibration_assimilation.py` |
| Prerequisite | `src/crk1/mission_005_calibration_lineage_stress.py` |
| Tests | `tests/mission006/test_assimilation.py` |
| Sample receipt | `fixtures/crk1/sample_caa1_receipt.json` |
| SDK demo | `sdk/continuity-sdk/experiments/success/calibration_replay/` |

## Run

```python
from src.crk1.mission_006_calibration_assimilation import run_mission_006_calibration_assimilation

report = run_mission_006_calibration_assimilation()
assert report.passed
assert report.continuity_passed
```

```bash
python -m pytest tests/mission006/test_assimilation.py -v
```

## Deliverables

- [x] `fixtures/crk1/CAA1_continuity_assimilation_receipt.schema.json`
- [x] `tests/mission006/test_assimilation.py`
- [x] `docs/crk1/mission-006/MISSION-006-CONTINUITY-ASSIMILATION.md`
- [x] Example CAA-1 receipt (`fixtures/crk1/sample_caa1_receipt.json`)
- [x] SDK assimilation demo (`sdk/continuity-sdk/experiments/success/calibration_replay/`)

## Related

- [Mission #005 — Calibration Lineage Stress](../mission-005/MISSION-005-CALIBRATION-LINEAGE-STRESS.md)
- [CONTINUITY_OS_ARCHITECTURE.md](../continuity-os/CONTINUITY_OS_ARCHITECTURE.md)
- [CRC v0.1 — Canonical Runtime Contract](../CRC-V0.1-CANONICAL-RUNTIME-CONTRACT.md)
