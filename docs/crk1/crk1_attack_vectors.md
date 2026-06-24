# CRK-1 Insulation Attack Vectors

Version 1.0

This document enumerates all known classes of insulation attacks that must be
detected and rejected by a CRK-1-compliant runtime.

**Canonical test suite:** `tests/crk1/test_insulation_attack_suite.py`  
**Simulator:** `src/crk1/attack_simulator.py`  
**Machine-readable invariants:** `docs/crk1/crk1_invariants.yaml`

---

## 1. Outcome Suppression Attacks

**Goal:** Prevent the system from generating or retaining Outcomes.

### 1.1 Drop-Outcome Attack

- Delete Outcome objects.
- Replace Outcome with null.
- Skip Outcome creation during execution.

**Guard:** K1.1 — `delete(Outcome)` forbidden. K0.1 — execution must produce Outcome.

### 1.2 Non-Replayable Outcome Attack

- Set `replayable = false`.
- Produce Outcomes that cannot be replayed.

**Guard:** K0.2 schema const; K1.3 forbidden mutation.

---

## 2. Evidence Suppression Attacks

**Goal:** Prevent Evidence from entering future judgment cycles.

### 2.1 Evidence Quarantine Attack

- Mark Evidence as non-admissible.
- Move Evidence to a non-visible namespace.

**Guard:** K1.2, K1.4 — quarantine forbidden.

### 2.2 Evidence Reinterpretation Attack

- Rewrite Evidence to remove causal linkage.
- Strip `source_outcome_id`.

**Guard:** K0.3 — replay must yield linked, admissible Evidence.

---

## 3. Lineage Escape Attacks

**Goal:** Allow successors to avoid ancestor consequences.

### 3.1 Fork-Without-History Attack

- Create a new Identity that does not inherit ancestor Evidence.

**Guard:** K3.1 — child must inherit ancestor Evidence.

### 3.2 Selective-Visibility Attack

- Child identity requests Evidence but excludes ancestor lineage.

**Guard:** K2.3, K3.1 — lineage visibility rules.

---

## 4. Judgment Decoupling Attacks

**Goal:** Allow Decisions to be made without exposure to consequences.

### 4.1 Evidence-Free Decision Attack

- Create Decisions with empty `input_evidence_ids`.

**Guard:** K2.2 — `input_evidence_ids.length >= 1`.

### 4.2 Identity-Free Decision Attack

- Create Decisions without `identity_id`.

**Guard:** K2.1 — `identity_id` required.

---

## 5. Replay Bypass Attacks

**Goal:** Prevent Outcomes from re-entering the Evidence pool.

### 5.1 Replay-Block Attack

- Override replay function to return null.

**Guard:** K0.3 — `assert_replay_produces_evidence`.

### 5.2 Replay-Rewrite Attack

- Replay Outcome but produce Evidence with `admissible_for_decision = false`.

**Guard:** K1.4 schema const; `assert_evidence_admissible`.

---

## 6. Constitutional Rewrite Attacks

**Goal:** Modify invariants to allow insulation.

### 6.1 Invariant Downgrade Attack

- Change schema to allow non-admissible Evidence.

**Guard:** JSON Schema `const: true` on admissibility fields; K5 mutation admissibility.

### 6.2 Invariant Removal Attack

- Remove lineage coupling rules.

**Guard:** K5.5 — `lineage_rules = disable` forbidden.

---

## 7. Governance Capture Attacks

**Goal:** Use governance to authorize insulation.

### 7.1 Governance-Approved Insulation

- Propose a law that allows Evidence suppression.
- Propose a law that allows lineage resets.

**Note:** Under CRK-1, these proposals are unconstitutional and must be rejected at validation time (K3.3, K4, K5).

---

## Badge mapping

| Attack class | Badge |
|--------------|-------|
| General insulation | `crk1_continuity_badges/insulation_detected.svg` |
| Lineage escape | `crk1_continuity_badges/lineage_break_detected.svg` |
| Evidence quarantine | `crk1_continuity_badges/evidence_suppression_detected.svg` |
| Suite pass | `crk1_continuity_badges/continuity_pass.svg` |
| Suite fail | `crk1_continuity_badges/continuity_fail.svg` |
