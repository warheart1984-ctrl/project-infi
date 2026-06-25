# CDP-1 Adversarial Suite

Attack classes for external red-team evaluation of CDP-1 / CEP.

## A. Isolation Attacks

| Attack | Description | Expected failure | Governance response |
|--------|-------------|------------------|---------------------|
| **Fake isolation** | Tamper `isolation_proof` after run | `validate_caa1` rejects proof bundle | FAIL structural validation |
| **Steward contamination** | S₂ participated in original event | `compute_isolation_proof` raises | Invalidate run before receipt |
| **Cross-steward leakage** | S₂ observes another steward's traces | ΔA inflated without valid isolation | Isolation audit FAIL |

**Fixtures:** `experiments/failure/assimilation_redteam/forged_isolation.test.ts`, `tests/mission006/test_assimilation_redteam.py`

## B. Lineage Attacks

| Attack | Description | Expected failure | Governance response |
|--------|-------------|------------------|---------------------|
| **CRR-1 tampering** | Alter calibration receipt hash | Lineage hash mismatch | FAIL lineage validation |
| **CLG-1 breakage** | Orphan or missing parent nodes | Reconstruction incomplete | FAIL reconstruction |
| **Lineage reordering** | Reorder events in CLG-1 | Hash mismatch vs canonical | FAIL lineage validation |

**Fixtures:** `lineage_tampering.test.ts`, `experiments/failure/broken_lineage/`

## C. Measurement Attacks

| Attack | Description | Expected failure | Governance response |
|--------|-------------|------------------|---------------------|
| **ΔA fabrication** | Set `continuity_passed` when ΔA < τA | Schema/logic validation | FAIL metric stage |
| **Task substitution** | Post-test uses different contradiction class | Contradiction-class mismatch | FAIL mission manifest |
| **Threshold gaming** | τA below noise floor | Governance minimum enforcement | Reject threshold |

**Fixtures:** `delta_mismatch.test.ts`, `experiments/failure/missing_crr/`

## D. Proof Attacks

| Attack | Description | Expected failure | Governance response |
|--------|-------------|------------------|---------------------|
| **Proof bundle forgery** | Invalid `proof_bundle` hash | Recomputation mismatch | FAIL proof integrity |
| **Hash collision attempts** | Non-hex or wrong-length hashes | Schema validation | FAIL structural |

## E. Governance Attacks

| Attack | Description | Expected failure | Governance response |
|--------|-------------|------------------|---------------------|
| **Veto suppression** | Hide review steward objection | Charter violation | Mandatory re-evaluation |
| **Steward collusion** | Shared answers across S₂ runs | Cross-steward entropy check | Invalidate replication claim |

## Running the Suite

```bash
python -m pytest tests/mission006/test_assimilation_redteam.py -v
cd sdk/continuity-sdk && npm test
```
