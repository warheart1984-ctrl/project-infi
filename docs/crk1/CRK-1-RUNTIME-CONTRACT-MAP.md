# CRK‑1 Runtime Contract Map

Version 1.0

Maps each kernel law K0–K12 to concrete runtime responsibilities.

**Related:** `CRK-1-UNIFIED-KERNEL-SPECIFICATION.md` · `CRK-1-CONTINUITY-PROOF-SKETCH.md` · `src/crk1/` · `src/continuity/constitutional_runtime.py`

---

## Objects

- **IdentityObject** — `src/continuity/identity_object.py`
- **DecisionObject** — `src/continuity/decision_ledger.py` (`DecisionRecord`); facade: `CRK1Decision`
- **OutcomeObject** — `src/continuity/outcome_ledger.py`; facade: `CRK1Outcome`
- **EvidenceObject** — `src/continuity/evidence_ledger.py` (`EvidenceRecord`); facade: `CRK1Evidence`
- **InterpretationObject** — `src/crk1/semantic_objects.py` (`InterpretationObject`); runtime: `CRK1Interpretation`

---

## Contracts

Each method is a constitutional gate: it must fail if its associated invariants would be violated.

### EvidenceContract

| Method | Enforces | Implementation anchor |
|--------|----------|------------------------|
| `admit_evidence(e: EvidenceObject)` | K0 (Outcome→Evidence), K3 (no blocked evidence), K4 (preserve exposure) | `assert_evidence_admissible`, `EvidenceContract.check_decision_evidence` |
| `replay_outcome(o: OutcomeObject) -> EvidenceObject` | K0, K1 (no severing Outcome→Evidence) | `CRK1Runtime.replay_outcome`, `assert_outcome_replayable`, `assert_replay_produces_evidence` |

### GovernanceContract

| Method | Enforces | Implementation anchor |
|--------|----------|------------------------|
| `propose_mutation(mutation)` | K5 (mutation admissibility) | `mutation_admissible`, `assert_mutation_admissible`, `Governance.propose_kernel_amendment` |
| `ratify_mutation(mutation)` | K4 (consequence preservation), K6 (CE drift envelope) | `apply_amendment_with_drift_check`, `validate_consequence_preservation`, `validate_drift_envelope` |
| `audit_constitution()` | CE(S) ≥ 0, K3 (no insulation) | `consequence_exposure`, `IntegrityMonitor`, `InsulationAttackSimulator` |

### RuntimeContract

| Method | Enforces | Implementation anchor |
|--------|----------|------------------------|
| `execute_decision(d: DecisionObject) -> OutcomeObject` | K0 (Decision→Outcome), K2 (judgment coupling) | `ConstitutionalRuntime.execute_decision`, `CRK1Runtime.propose_and_execute`, `assert_decision_has_identity`, `assert_decision_has_evidence` |
| `advance_epoch()` | K6 (CE drift envelope), K11 (SE drift envelope) | `ConstitutionalRuntime.advance_epoch`, `SemanticExposureMonitor.simulate_drift`, `DriftSimulator.test_drift` |

### SemanticContract (implicit in runtime)

| Method | Enforces | Implementation anchor |
|--------|----------|------------------------|
| `register_interpretation(i: InterpretationObject)` | K7 (pluralism), K8 (prediction binding), K9 (anti‑monoculture) | `SemanticLayer.create_interpretation`, `_assert_k7`, `_assert_k9` |
| `generate_prediction(i, e) -> PredictionObject` | K8 | `SemanticLayer.generate_prediction`, `PredictionObject` |
| `reconstruct_view(i, e) -> ReconstructionObject` | K10 (adversarial reconstruction) | `SemanticLayer.reconstruct`, `ReconstructionObject` |
| `measure_SE() -> float` | K12 (SE(S) > 0) | `SemanticExposureMonitor.measure_exposure` |

---

## Invariant index (K0–K12)

| Law | Layer | Primary gate(s) |
|-----|-------|-----------------|
| K0 | Transmission | `execute_decision`, `replay_outcome` |
| K1 | Transmission | `replay_outcome`, runtime assertions |
| K2 | Transmission | `execute_decision`, lineage exposure |
| K3 | Preservation | `audit_constitution`, anti-insulation proofs |
| K4 | Preservation | `ratify_mutation`, `admit_evidence` |
| K5 | Preservation | `propose_mutation` |
| K6 | Preservation | `ratify_mutation`, `advance_epoch`, `DriftSimulator` |
| K7 | Assimilation | `register_interpretation` |
| K8 | Assimilation | `register_interpretation`, `generate_prediction` |
| K9 | Assimilation | `register_interpretation` (weight normalization) |
| K10 | Assimilation | `reconstruct_view` |
| K11 | Assimilation | `advance_epoch`, `SemanticExposureMonitor` history |
| K12 | Assimilation | `measure_SE` |

---

## Ledgers and audit surfaces

| Surface | Role |
|---------|------|
| `CRK1SemanticLedger` | Canonical record of interpretations, predictions, reconstructions |
| `CRK1MutationLedger` | Constitutional mutation history with CE/SE before/after |
| `DriftVisualizer` | Founder-independent ASCII CE/SE continuity dashboard |
| `SemanticReproductionHarness` | Founder-independent K7–K12 reproduction test |
