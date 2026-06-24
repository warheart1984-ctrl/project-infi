# M3-B — Red-Team Attack Suite

Version 1.0 — CRK-1 Mission #003

**Purpose:** Systematically try to break continuity (mechanical, structural, semantic, founder).

**Implementation:** `src/crk1/red_team_protocol.py`  
**Tests:** `tests/crk1/test_mission_003_red_team.py`

Each attack applies a change, measures CE(S)/SE(S), checks K0–K12 + harness, and records a **Red-Team Report** entry.

**Pass condition:** All unconstitutional attacks are **blocked** (`PASS`) or **rejected** (`REJECTED`). Zero `FAILED`.

---

## B1 — Mechanical Insulation (K0–K2)

| ID | Attack |
|----|--------|
| B1-01 | Drop Outcomes before Evidence |
| B1-02 | Create non-replayable Outcomes |
| B1-03 | Bypass EvidenceContract (quarantine) |
| B1-04 | Lineage escape |
| B1-05 | Decision without evidence |
| B1-06 | Replay bypass |

**Expected:** K0–K2 stop all attempts (`InsulationAttackSimulator`).

---

## B2 — Structural Insulation (K3–K6)

| ID | Attack |
|----|--------|
| B2-01 | Shadow Outcome path (disable replayability mutation) |
| B2-02 | Policy non-admissible Evidence |
| B2-03 | Block consequence propagation |
| B2-04 | Governance bypass (direct amendment) |
| B2-05 | Governance without evidence |
| B2-06 | Shadow Outcome (no outcome on execute) |

**Expected:** K4–K6 + `DriftSimulator` reject insulating mutations.

---

## B3 — Semantic Insulation (K7–K12)

| ID | Attack |
|----|--------|
| B3-01 | Single frame weight 1.0 |
| B3-02 | Remove all adversarial frames |
| B3-03 | Interpretations with no predictions |
| B3-04 | SE(S) forced toward 0 via weight games |
| B3-05 | Semantic exposure audit (baseline PASS) |

**Expected:** `SemanticDriftAuditor` + K7–K12 prevent semantic capture.

---

## B4 — Founder Capture

| ID | Attack |
|----|--------|
| B4-01 | Hidden config not in ledgers (packet completeness) |
| B4-02 | Invariants only in docs/comments (yaml registry) |
| B4-03 | Founder-only override (reproduction harness) |
| B4-04 | Non-ledgered interpretive state |
| B4-05 | Magic founder-only decision bypass |

**Expected:** M3-A packet + reproduction harness expose gaps.

---

## Running

```bash
uv run pytest tests/crk1/test_mission_003_red_team.py -q
```

```python
from src.crk1.red_team_protocol import RedTeamProtocol

report = RedTeamProtocol(runtime).run_all()
print(report.summary())
```
