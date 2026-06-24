# M3-E — Reproduction Certification Protocol

Version 1.0 — CRK-1 Mission #003

**Purpose:** Turn external reproduction + red-team into a formal **CRK-1 v1.0 Compliant** stamp.

**Implementation:** `src/crk1/reproduction_certifier.py`  
**CLI:** `tools/run_mission_003_certification.py`

---

## Protocol Phases

### E1 — Packet Delivery

External team receives **only M3-A** (no side-channel explanations).

Verify: `verify_packet_artifacts()` from `mission_003_packet.py`

### E2 — Independent Reconstruction

Implement CRK-1 from A1–A7. Run:

- `ExternalReproductionHarness.run_all()`
- `SemanticReproductionHarness.run()` (A7 / K7–K12)

Document: object/contract mapping, K0–K12 checks, CE/SE implementations.

### E3 — Red-Team Execution

Run M3-B and M3-C:

```python
RedTeamProtocol(runtime).run_all()
DriftStressProtocol(runtime).run_all()
```

### E4 — Evidence Submission

Submit:

- Code
- Test logs (`pytest tests/crk1/test_mission_003_*.py`)
- CE/SE drift results from `DriftStressReport`
- Red-team outcomes from `RedTeamReport`
- Filled Continuity Failure Catalog (attacks tried vs blocked)

### E5 — Certification Decision

Governance body checks:

- All K0–K12 enforced
- All continuity failures blocked or detected (M3-D)
- No founder-only assumptions

If passed → **CRK-1 v1.0 Compliant** + signed Reproduction Certificate.

```bash
uv run python tools/run_mission_003_certification.py --json
```

---

## Certification Levels

| Level | Requirement |
|-------|-------------|
| **R1** | Genesis kernel + semantic ledger reconstructible |
| **R2** | K0–K12 executable (yaml + FIT + A7 harness) |
| **R3** | External reproduction harness PASS |
| **R4** | Red-team B1–B4 PASS |
| **R5** | Drift stress C1–C3 PASS |
| **CERTIFIED** | R1 ∧ R2 ∧ R3 ∧ R4 ∧ R5 |

---

## Certification Record Schema

```json
{
  "mission": "003",
  "version": "1.0",
  "certified": true,
  "levels": {
    "R1_substrate": true,
    "R2_invariants": true,
    "R3_reproduction": true,
    "R4_red_team": true,
    "R5_drift": true
  },
  "kernel_ledger_hash": "<sha256>",
  "semantic_ledger_signature": "<sha256>",
  "packet_fingerprint": "<sha256 of M3-A artifacts>",
  "implementation_hash": "<same as packet_fingerprint for reference build>",
  "timestamp": "<iso8601>",
  "drift_tests_run": 9,
  "drift_tests_passed": 9
}
```

---

## Revocation

Certification revoked if:

- Any red-team attack returns `FAILED`
- CE(S) or SE(S) decreases under a governance-admitted mutation
- Reproduction harness cannot rebuild from ledgers alone
- Invariant yaml diverges from executable checks without ledgered amendment

---

## Programmatic Issue

```python
from src.crk1.reproduction_certifier import Mission003Certifier

cert = Mission003Certifier(runtime).certify()
print(cert.to_json())
```
