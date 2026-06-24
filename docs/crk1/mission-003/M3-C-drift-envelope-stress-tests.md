# M3-C — Drift Envelope Stress Tests

Version 1.0 — CRK-1 Mission #003

**Purpose:** Prove CE(S) and SE(S) cannot be driven down by any governance-admissible mutation.

**Implementation:** `src/crk1/drift_stress_protocol.py`  
**Batteries:** `src/crk1/mission_003_packet.py`  
**Tests:** `tests/crk1/test_mission_003_drift_stress.py`

---

## Core Harness

```python
from src.crk1.drift_stress_protocol import DriftStressProtocol

report = DriftStressProtocol(runtime).run_all()
```

Uses `DriftSimulator.test_drift_with_exposure()` per mutation.

---

## Mutation Categories

### C1 — Benign mutations

Refactors, parameter tweaks, admissible interpretive drift.

- governance quorum adjustment
- constitutional quorum tweak
- interpretation drift (empty change set)

**Expected:** CE_after ≥ CE_before, SE_after ≥ SE_before.

### C2 — Risky but honest mutations

New features, new interpretive frames, new governance rules.

- higher quorum governance change
- interpretive drift with justification

**Expected:** passes governance envelope or rejects cleanly.

### C3 — Malicious mutations

Explicit attempts to reduce exposure — **must reject**.

- `Outcome.replayable: false`
- `block_consequence_propagation: true`
- `lineage_rules: disable`
- `insulate_judgment_from_outcomes: true`

---

## Checks (per mutation)

| Check | Law |
|-------|-----|
| CE_after ≥ CE_before | K6 |
| SE_after ≥ SE_before | K11 |
| If violated → rejected | K5, GovernanceContract |

Each result is recorded in `CRK1MutationLedger` when using `run_all(record_ledger=True)`.

---

## Stress Success Condition

> No mutation that passes governance can reduce CE(S) or SE(S).

```bash
uv run pytest tests/crk1/test_mission_003_drift_stress.py -q
```
