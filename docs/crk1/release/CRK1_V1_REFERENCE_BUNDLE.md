# CRK-1 v1.0 Reference Implementation Bundle Outline

Engineering handoff: exact structure external operators receive.  
Paths below are relative to the `project-infi` repository root.

---

## 1. Kernel specification

### 1.1 CRK-1 Kernel Codex (K0–K12)

| Bundle name | Repo path |
|-------------|-----------|
| `crk1_kernel_codex.md` | `docs/crk1/crk1_kernel_codex.md` |

### 1.2 Constitutional object schemas

| Bundle name | Repo path |
|-------------|-----------|
| `IdentityObject.json` | `fixtures/crk1/identity_object.schema.json` |
| `DecisionObject.json` | `fixtures/crk1/decision_object.schema.json` |
| `OutcomeObject.json` | `fixtures/crk1/outcome_object.schema.json` |
| `EvidenceObject.json` | `fixtures/crk1/evidence_object.schema.json` |
| `InterpretationObject.json` | `fixtures/crk1/interpretation_object.schema.json` |

### 1.3 Constitutional contracts

| Bundle name | Repo path |
|-------------|-----------|
| Evidence / Governance / Runtime / Semantic | `docs/crk1/CRK-1-RUNTIME-CONTRACT-MAP.md` |

---

## 2. Runtime components

| Bundle name | Repo path |
|-------------|-----------|
| `crk1_minimal_runtime.py` | `src/crk1/crk1_minimal_runtime.py` |
| `crk1_semantic_replay_engine.py` | `src/crk1/semantic_replay_engine.py` |
| `crk1_drift_simulator.py` | `src/crk1/drift_simulator.py` |
| `crk1_governance_engine.py` | `src/crk1/crk1_governance_engine.py` |
| Production runtime facade | `src/crk1/runtime_facade.py` |

---

## 3. Ledgers

| Bundle name | Repo path |
|-------------|-----------|
| Kernel ledger entry | `src/crk1/kernel_ledger.py` |
| Mutation ledger | `src/crk1/mutation_ledger.py` |
| Semantic ledger | `src/crk1/semantic_ledger.py` |

---

## 4. Verification and testing

| Bundle name | Repo path |
|-------------|-----------|
| `crk1_reproduction_harness.py` | `src/crk1/external_reproduction_harness.py` |
| `crk1_redteam_suite.py` | `src/crk1/crk1_redteam_suite.py` |
| `crk1_drift_stress.py` | `src/crk1/drift_stress_protocol.py` |
| `continuity_failure_catalog.md` | `docs/crk1/mission-003/M3-D-continuity-failure-catalog.md` |
| Test suite | `tests/crk1/` |

---

## 5. Governance infrastructure

| Bundle name | Repo path |
|-------------|-----------|
| `governance_receipt.schema.json` | `fixtures/crk1/governance_receipt_header.schema.json` |
| `crk1_governance_receipt_verifier.py` | `src/crk1/governance_receipt_verifier.py` |
| `crk1_governance_receipt_merkleizer.py` | `src/crk1/governance_receipt_merkleizer.py` |
| `crk1_governance_receipt_index.py` | `src/crk1/governance_receipt_index.py` |

---

## 6. Visual and documentation assets

| Bundle name | Repo path |
|-------------|-----------|
| `crk1_runtime_diagram.svg` | `docs/crk1/crk1_runtime_diagram.svg` |
| `crk1_kernel_minimap.svg` | `docs/crk1/crk1_kernel_minimap.svg` |
| D-3 seal (format + certifier) | `docs/crk1/mission-003/D3-SEAL-reproduction-certificate.md`, `src/crk1/d3_reproduction_certificate.py` |
| `crk1_release_manifest.md` | `docs/crk1/release/CRK1_V1_RELEASE_MANIFEST.md` |

---

## 7. Certification materials

| Bundle name | Repo path |
|-------------|-----------|
| `crk1_reproduction_protocol.md` | `docs/crk1/mission-003/M3-E-reproduction-certification-protocol.md` |
| M3-A external packet | `docs/crk1/mission-003/M3-A-external-reproduction-packet.md` |
| Governance receipt header template | `fixtures/crk1/governance_receipt_header.schema.json` |

---

## 8. Post-release integration (not in v1.0 bundle — roadmap)

| Component | Spec | Implementation status |
|-----------|------|------------------------|
| Continuity API v0.1 | `docs/crk1/roadmap/CONTINUITY_API_V0_1.md` | Not yet shipped |
| CRK-Explorer | `docs/crk1/roadmap/CRK_EXPLORER_UI_SPEC.md` | Not yet shipped |
| DARZ-VR Unity renderer | `docs/crk1/roadmap/DARZ_VR_UNITY_SPEC.md` | Not yet shipped |
