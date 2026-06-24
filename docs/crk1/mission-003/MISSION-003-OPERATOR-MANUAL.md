# Mission #003 — Operator Manual (v1.0)

**Objective:** Rebuild CRK-1 from the Reproduction Packet, run the test harness, validate invariants, and issue a D-3 Seal if all tests pass.

**Audience:** External stewards (non-founders)  
**Runnable checklist:** [MISSION-003-REPRODUCTION-CHECKLIST.md](MISSION-003-REPRODUCTION-CHECKLIST.md)  
**Seal schema:** `fixtures/crk1/reproduction_seal.schema.json`

---

## Phase 0 — Preparation

1. Obtain the Reproduction Packet (`RP-CRK1-v1.0`).
2. Verify packet integrity (hash + artifact manifest).
3. Provision a **clean** execution environment:
   - No founder-only code paths
   - No pre-seeded constitutional state
   - No oral-tradition dependencies
4. Disable external dependencies except those listed in the packet (Python stdlib + repo `pyproject` deps).

**Verify:**

```bash
python -c "from src.crk1.mission_003_packet import verify_packet_artifacts; assert verify_packet_artifacts()[0]"
```

---

## Phase 1 — Rebuild CRK-1

Build components exactly as specified in M3-A:

| Component | Reference |
|-----------|-----------|
| Object Model | `fixtures/crk1/v01/*.schema.json`, `src/crk1/models/` |
| Governance Engine | `src/crk1/governance_engine.py`, `crk1_governance_engine.py` |
| Continuity Graph | append-only Identity→Decision→Outcome→Evidence→Interpretation |
| Receipt Engine | `governance_receipt_*`, Merkle: `governance_receipt_merkleizer.py` |
| Drift & Metrics | CE, SE, RAI, RDI, CFE — `consequence_lattice.py`, `drift_simulator.py` |
| Kernel Challenge Path | Mission #004 / KΩ — `kernel_challenge_path.py` |
| Event Stream | ledger mutations + receipt anchoring |

**Success condition:** Runtime compiles, initializes (`CRK1Runtime.bootstrap()`), and exposes programmatic continuity operations.

---

## Phase 2 — Execute test harness

### 2.1 Invariant enforcement

- Submit valid and invalid actions.
- Confirm governance accepts only invariant-compliant actions.
- Confirm refusal receipts include invariant context.

**Tests:** `test_crk1_invariants.py`, `test_crk1_wire_v01.py`

### 2.2 Governance refusal

- Attempt to bypass governance (direct ledger patch, receipt-less mutation).
- Confirm all bypass attempts fail deterministically.

**Tests:** `test_crk1_governance_engine.py`, `test_governance_receipt_audit.py`

### 2.3 Semantic capture

- Attempt interpretive layers that block contradiction.
- Confirm K7–K12 prevent insulation.

**Tests:** `SemanticReproductionHarness`, `test_mission_003_drift_stress.py`

### 2.4 Governance bypass

- Attempt implementation-level bypass (hidden state, shadow mutation).
- Confirm governance cannot be circumvented.

**Tests:** `test_crk1_redteam_suite.py` (B1–B4)

### 2.5 Continuity graph

- Create Identity → Decision → Outcome → Evidence → Interpretation chain.
- Confirm graph is correct, append-only, reconstructible.

**Tests:** `test_crk1_continuity.py`, wire v01 tests

### 2.6 Kernel challenge path

- Submit synthetic CF-events / kernel challenges.
- Confirm path accepts, evaluates, issues KCR.

**Tests:** `test_mission_004_005.py`, `test_komega_idc_mission003.py`

---

## Phase 3 — Validate founder independence

- [ ] No founder-specific assumptions required
- [ ] No oral tradition or undocumented behavior needed
- [ ] All behavior matches packet + schemas + harness output
- [ ] `oral_tradition_used: false` on seal

---

## Phase 4 — Issue D-3 Seal

### If all tests pass

1. Generate `ReproductionSeal` per schema (`type: ReproductionSeal`).
2. Set all `payload.tests_executed.*` to `PASS`.
3. Set `payload.results.all_passed: true`.
4. Link `reproduction_packet_id`, `test_harness_ids`, `governance_receipt_ids`.
5. Publish seal to continuity graph (when API available).
6. Emit event `REPRODUCTION_SEAL_ISSUED`.

**Sample:** `fixtures/crk1/sample_reproduction_seal.json`

### If any test fails

1. Log failure with pytest output and harness report.
2. Do **not** issue seal with `all_passed: true`.
3. If failure indicates invariant insufficiency → submit Kernel Challenge (Mission #004).

---

## Certification levels (reference)

| Level | Requirement |
|-------|-------------|
| R1 | Genesis kernel + semantic ledger reconstructible |
| R2 | K0–K12 executable |
| R3 | External reproduction harness PASS |
| R4 | Red-team B1–B4 PASS |
| R5 | Drift stress C1–C3 PASS |
| **CERTIFIED** | R1 ∧ R2 ∧ R3 ∧ R4 ∧ R5 |

See: `M3-E-reproduction-certification-protocol.md`

---

## Interpretation

A D-3 Seal is **not a badge**. It is a receipt proving CRK-1 is a scientific object rebuildable by non-founders. The burden of proof shifts to reality: succeed → demonstrated continuity substrate; fail → kernel must evolve.
