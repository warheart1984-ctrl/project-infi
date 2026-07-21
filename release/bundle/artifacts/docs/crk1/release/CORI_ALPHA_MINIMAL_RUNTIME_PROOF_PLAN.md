# CORI Alpha Minimal Runtime Proof Plan

**Release family:** CRK-1 companion specification  
**Status:** Draft  
**Depends on:** CIS Core v1.0, CIS Standards Traceability Matrix, CIS Conformance Suite Specification, CIS Launch Readiness Specification, CORI Alpha Proof Chain  
**Stewardship:** CIS release maintainers  
**Constitutional sections:** 1-5  
**Informative sections:** 6

---

## 1. Objective

Build the smallest runtime that can demonstrate the constitutional model in executable form.

The runtime is considered minimal only if it can prove the following capabilities end to end:

- Identity
- Evidence
- Constitutional State Record
- Constitutional Receipt
- Replay
- Conformance

## 2. Work slices

### 2.1 Identity slice

Implement a stable identity record for the proof surface.

Acceptance criteria:

- The runtime can create or load a canonical identity record.
- The identity record is traceable to a CIS requirement.
- The identity record is included in the evidence package.

### 2.2 Evidence slice

Implement evidence capture for the proof workflow.

Acceptance criteria:

- The runtime records objective evidence artifacts.
- Each evidence artifact is traceable to the governing requirement.
- Evidence can be inspected without private explanation.

### 2.3 Constitutional state record slice

Implement a governed state record for the proof workflow.

Acceptance criteria:

- The runtime can serialize a constitutional state record.
- The state record identifies the governed decision path.
- State transitions remain auditable.

### 2.4 Constitutional receipt slice

Implement receipt generation for the proof workflow.

Acceptance criteria:

- The runtime emits a constitutional receipt.
- The receipt references the governing evidence package.
- The receipt can be validated independently.

### 2.5 Replay slice

Implement deterministic replay for the proof workflow.

Acceptance criteria:

- The runtime can reconstruct the governed path from recorded inputs.
- Replay does not depend on hidden state or private explanation.
- Replay yields the same constitutional conclusion when inputs are unchanged.

### 2.6 Conformance slice

Implement conformance checks for the proof workflow.

Acceptance criteria:

- The runtime can validate the proof against the frozen baseline.
- Conformance output is objective and reproducible.
- Failures identify the specific governing gap.

## 3. Traceability rule

Each slice SHALL identify:

- the CIS requirement it implements
- the specification that owns it
- the evidence it produces
- the conformance tests that validate it
- the replay path that verifies it

## 4. Proof rule

The runtime proof is complete only when the full workflow can be executed, replayed, inspected, and independently verified through the release pipeline.

## 5. Acceptance summary

The minimal runtime proof is accepted when all six capabilities work together as a single governed workflow and the resulting proof is visible in the release bundle.

## 6. Concrete implementation checklist

The machine-readable companion for the checklist is `CORI_ALPHA_MINIMAL_RUNTIME_STATUS.spec.json`, validated against `CORI_ALPHA_STATUS.schema.json`.
The tiny rendered dashboard is `CORI_ALPHA_MINIMAL_RUNTIME_DASHBOARD.md`, generated from the same status companion.

| Slice | Owning CIS requirement(s) | Companion specification reference | Runtime components / files | Required APIs | Evidence produced | Constitutional receipts generated | Conformance tests | Replay validation | Acceptance criteria | Current status |
|---|---|---|---|---|---|---|---|---|---|---|
| Identity | `CORI Alpha is the first independently verifiable constitutional proof`; `Every CIS requirement traces through the full constitutional path` | `CORI_ALPHA_PROOF_CHAIN.md`, `CIS_STANDARDS_TRACEABILITY_MATRIX.md` | `src/governance/invariants.ts`, `src/governance/trace_store.ts`, `src/ledger/DurableLedger.ts`, `src/envelope/Envelope.ts` | `GovernedInvariantEngine.evaluate`, `InMemoryTraceStore.appendStep`, `InMemoryTraceStore.getTrace`, `DurableLedger.write` | Canonical identity record, trace record, envelope hash | `ReceiptBuilder.build`, `DurableLedger.writeReceipt` | `tests/release/cori-alpha-proof.test.ts`, `packages/aaes-governance/src/proofSurface.test.ts` | `EglReplay.replay`, `ReplayDriftDetector.detect` | Identity is canonical, traceable to a CIS requirement, and included in the evidence package | In Progress |
| Evidence | `CORI Alpha is the first independently verifiable constitutional proof`; `The conformance suite is generated from the traceability matrix source of truth` | `CORI_ALPHA_PROOF_CHAIN.md`, `CIS_CONFORMANCE_SUITE_SPECIFICATION.md` | `src/ledger/DurableLedger.ts`, `src/governance/trace_store.ts`, `packages/aaes-governance/src/evidenceGraph.ts` | `DurableLedger.write`, `DurableLedger.writeReceipt`, `InMemoryTraceStore.appendStep`, evidence graph builders | Evidence package, hashes, ledger line items, review records | `ReceiptBuilder.build`, `ReceiptSigner.sign` | `tests/release/cori-alpha-proof.test.ts`, `tests/release/cis-conformance-generation.test.ts` | `EglReplay.replay`, `ReplayDriftDetector.detect` | Every evidence artifact is objective, inspectable, and tied to the governing requirement | In Progress |
| Constitutional State Record | `CORI Alpha is the first independently verifiable constitutional proof`; `Every artifact carries consistent governance status, stewardship, versioning, traceability, and release lifecycle fields` | `GOVERNED_KNOWLEDGE_STORE_SPECIFICATION.md`, `CORI_ALPHA_PROOF_CHAIN.md` | `src/governance/invariants.ts`, `src/governance/policies.ts`, `src/ledger/DurableLedger.ts`, `src/ledger/Ledger.types.ts` | `GovernedInvariantEngine.evaluate`, `InMemoryTraceStore.getTrace`, `DurableLedger.write`, `DurableLedger.readAll` | Serialized state record, governed transition log, canonical state snapshot | `ReceiptBuilder.build`, `DurableLedger.writeReceipt` | `tests/release/cori-alpha-proof.test.ts`, `tests/release/artifact-governance.test.ts` | `EglReplay.replay`, `EnvelopeValidator.validate` | The state record identifies the governed decision path and stays auditable | In Progress |
| Constitutional Receipt | `CORI Alpha is the first independently verifiable constitutional proof`; `Launch readiness is governed by evidence rather than subjective judgment` | `CIS_LAUNCH_READINESS_SPECIFICATION.md`, `CORI_ALPHA_PROOF_CHAIN.md` | `src/receipts/Receipt.types.ts`, `src/receipts/ReceiptBuilder.ts`, `src/receipts/ReceiptVerifier.ts`, `src/receipts/ReceiptSigner.ts`, `src/ledger/DurableLedger.ts` | `ReceiptBuilder.build`, `ReceiptVerifier.verify`, `ReceiptSigner.sign`, `DurableLedger.writeReceipt` | Signed receipt, receipt hash, verification timestamp, release evidence pointer | `DurableLedger.writeReceipt`, `ReceiptBuilder.build` | `tests/release/cori-alpha-proof.test.ts`, `tests/release/release-pipeline.test.ts` | `EglReplay.replay`, `ReplayDriftDetector.detect` | The receipt verifies independently and links back to the evidence package | In Progress |
| Replay | `CORI Alpha is the first independently verifiable constitutional proof`; `The conformance suite validates constitutional, replay, receipt, trust, and acceptance criteria` | `CIS_CONFORMANCE_SUITE_SPECIFICATION.md`, `CORI_ALPHA_PROOF_CHAIN.md` | `src/replay/EglReplay.ts`, `src/replay/ReplayDriftDetector.ts`, `src/envelope/EnvelopeValidator.ts` | `EglReplay.replay`, `ReplayDriftDetector.detect`, `EnvelopeValidator.validate` | Replay artifact, drift report, validation output, replayable ledger path | `ReceiptBuilder.build`, `DurableLedger.writeReceipt` | `tests/release/cori-alpha-proof.test.ts`, `tests/release/release-pipeline.test.ts` | `EglReplay.replay`, `ReplayDriftDetector.detect`, `EnvelopeValidator.validate` | Replay reconstructs the governed path without hidden state or private explanation | In Progress |
| Conformance | `The conformance suite is generated from the traceability matrix source of truth`; `CORI Alpha is the first independently verifiable constitutional proof` | `CIS_STANDARDS_TRACEABILITY_MATRIX.md`, `CIS_CONFORMANCE_SUITE_SPECIFICATION.md`, `CIS_CONFORMANCE_SUITE_INPUT.spec.json` | `packages/aaes-governance/src/crec.ts`, `packages/aaes-governance/src/evidenceGraph.ts`, `tests/release/cis-conformance-generation.test.ts`, `tests/release/cori-alpha-proof.test.ts` | `generateCisConformanceSuiteInput`, `deriveCisConformanceSuiteInput`, conformance comparisons | Conformance input, validation families, acceptance criteria, conformance report | `ReceiptBuilder.build`, `DurableLedger.writeReceipt` | `tests/release/cis-conformance-generation.test.ts`, `tests/release/cori-alpha-proof.test.ts` | `EglReplay.replay`, `ReplayDriftDetector.detect` | The conformance result is objective, reproducible, and aligned with the traceability matrix | In Progress |

## 7. Implementation ordering

1. Identity and Evidence establish the canonical proof surface and persistence model.
2. Constitutional State Record and Constitutional Receipt make the workflow governed and auditable.
3. Replay and Conformance prove that the workflow can be reconstructed and validated independently.
4. The release bundle then exposes the proof surfaces through the governed release pipeline.

## 8. Live status derivation

Slice status SHOULD be derived from objective execution evidence rather than manually maintained.

Each slice status MAY move through `Not Started`, `In Progress`, and `Complete` based on the following evidence gates:

- Build verification
- Test verification
- Runtime verification
- Conformance verification
- Replay verification
- Evidence package generation

When the evidence gates are complete, the plan SHOULD behave as a live constitutional dashboard rather than a static checklist.

## 9. Machine-readable outputs

Every completed slice SHOULD emit:

- a machine-readable Constitutional Receipt
- a machine-readable Evidence Package
- a machine-readable Conformance Record
- a machine-readable Replay Verification Record
- a verification timestamp

Those outputs SHOULD be assembled automatically into the CORI Alpha proof package from verified runtime artifacts.

The intended evidence flow is:

Runtime -> Receipts -> Evidence Packages -> Conformance Records -> Slice Status -> Dashboard -> Release Evidence

## 10. Informative note

This plan is intentionally small.
It is designed to validate the constitutional model in executable form before any further runtime expansion.
