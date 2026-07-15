# CORI Alpha Minimal Runtime Dashboard

**Source:** [CORI_ALPHA_MINIMAL_RUNTIME_STATUS.spec.json](CORI_ALPHA_MINIMAL_RUNTIME_STATUS.spec.json)
**Generated:** 2026-07-12T23:07:53.653Z
**Purpose:** Machine-readable status companion for the CORI Alpha minimal runtime proof slices.
**Status:** Draft
**Derived from:** CORI_ALPHA_MINIMAL_RUNTIME_PROOF_PLAN.md

## Status Model

Allowed states: Not Started, In Progress, Evidence Pending, Verified, Complete

| State | Count |
|---|---|
| Not Started | 0 |
| In Progress | 6 |
| Evidence Pending | 0 |
| Verified | 0 |
| Complete | 0 |

## Slice Overview

| Slice ID | Slice Name | Current Status | Owning CIS Requirement(s) | Dependencies | Last Verification Timestamp |
|---|---|---|---|---|---|
| identity | Identity | In Progress | CORI Alpha is the first independently verifiable constitutional proof; Every CIS requirement traces through the full constitutional path | CIS Core v1.0; CIS_STANDARDS_TRACEABILITY_MATRIX.md; src/governance/invariants.ts | Not recorded |
| evidence | Evidence | In Progress | CORI Alpha is the first independently verifiable constitutional proof; The conformance suite is generated from the traceability matrix source of truth | identity; CIS_CONFORMANCE_SUITE_SPECIFICATION.md; src/ledger/DurableLedger.ts | Not recorded |
| constitutional-state-record | Constitutional State Record | In Progress | CORI Alpha is the first independently verifiable constitutional proof; Every artifact carries consistent governance status, stewardship, versioning, traceability, and release lifecycle fields | identity; evidence; GOVERNED_KNOWLEDGE_STORE_SPECIFICATION.md | Not recorded |
| constitutional-receipt | Constitutional Receipt | In Progress | CORI Alpha is the first independently verifiable constitutional proof; Launch readiness is governed by evidence rather than subjective judgment | evidence; constitutional-state-record; CIS_LAUNCH_READINESS_SPECIFICATION.md | Not recorded |
| replay | Replay | In Progress | CORI Alpha is the first independently verifiable constitutional proof; The conformance suite validates constitutional, replay, receipt, trust, and acceptance criteria | constitutional-state-record; constitutional-receipt; src/replay/EglReplay.ts | Not recorded |
| conformance | Conformance | In Progress | The conformance suite is generated from the traceability matrix source of truth; CORI Alpha is the first independently verifiable constitutional proof | CIS_STANDARDS_TRACEABILITY_MATRIX.md; CIS_CONFORMANCE_SUITE_SPECIFICATION.md; CIS_CONFORMANCE_SUITE_INPUT.spec.json | Not recorded |

## Slice Artifacts

| Slice ID | Constitutional Receipt | Evidence Package | Conformance Record | Replay Verification Record |
|---|---|---|---|---|
| identity | Not recorded | Not recorded | Not recorded | Not recorded |
| evidence | Not recorded | Not recorded | Not recorded | Not recorded |
| constitutional-state-record | Not recorded | Not recorded | Not recorded | Not recorded |
| constitutional-receipt | Not recorded | Not recorded | Not recorded | Not recorded |
| replay | Not recorded | Not recorded | Not recorded | Not recorded |
| conformance | Not recorded | Not recorded | Not recorded | Not recorded |

## Verification Details

| Slice Key | Gate | Status | Evidence |
|---|---|---|---|
| identity-build | Build | In Progress | release/build-release.ts; release/package-release.ts |
| identity-test | Test | In Progress | tests/release/cori-alpha-proof.test.ts; tests/release/release-pipeline.test.ts |
| identity-runtime | Runtime | In Progress | src/governance/invariants.ts; src/governance/trace_store.ts; src/ledger/DurableLedger.ts; src/envelope/Envelope.ts |
| identity-conformance | Conformance | In Progress | CIS_STANDARDS_TRACEABILITY_MATRIX.md; CIS_CONFORMANCE_SUITE_SPECIFICATION.md |
| identity-replay | Replay | In Progress | src/replay/EglReplay.ts; src/replay/ReplayDriftDetector.ts |
| evidence-build | Build | In Progress | release/build-release.ts; release/package-release.ts |
| evidence-test | Test | In Progress | tests/release/cori-alpha-proof.test.ts; tests/release/cis-conformance-generation.test.ts |
| evidence-runtime | Runtime | In Progress | src/ledger/DurableLedger.ts; src/governance/trace_store.ts; packages/aaes-governance/src/evidenceGraph.ts |
| evidence-conformance | Conformance | In Progress | CIS_STANDARDS_TRACEABILITY_MATRIX.md; CIS_CONFORMANCE_SUITE_INPUT.spec.json |
| evidence-replay | Replay | In Progress | src/replay/EglReplay.ts; src/replay/ReplayDriftDetector.ts |
| constitutional-state-record-build | Build | In Progress | release/build-release.ts; release/package-release.ts |
| constitutional-state-record-test | Test | In Progress | tests/release/cori-alpha-proof.test.ts; tests/release/artifact-governance.test.ts |
| constitutional-state-record-runtime | Runtime | In Progress | src/governance/invariants.ts; src/governance/policies.ts; src/ledger/DurableLedger.ts; src/ledger/Ledger.types.ts |
| constitutional-state-record-conformance | Conformance | In Progress | CIS_STANDARDS_TRACEABILITY_MATRIX.md; GOVERNED_KNOWLEDGE_STORE_SPECIFICATION.md |
| constitutional-state-record-replay | Replay | In Progress | src/replay/EglReplay.ts; src/envelope/EnvelopeValidator.ts |
| constitutional-receipt-build | Build | In Progress | release/build-release.ts; release/package-release.ts |
| constitutional-receipt-test | Test | In Progress | tests/release/cori-alpha-proof.test.ts; tests/release/release-pipeline.test.ts |
| constitutional-receipt-runtime | Runtime | In Progress | src/receipts/Receipt.types.ts; src/receipts/ReceiptBuilder.ts; src/receipts/ReceiptVerifier.ts; src/receipts/ReceiptSigner.ts; src/ledger/DurableLedger.ts |
| constitutional-receipt-conformance | Conformance | In Progress | CIS_LAUNCH_READINESS_SPECIFICATION.md; CIS_CONFORMANCE_SUITE_SPECIFICATION.md |
| constitutional-receipt-replay | Replay | In Progress | src/replay/EglReplay.ts; src/replay/ReplayDriftDetector.ts |
| replay-build | Build | In Progress | release/build-release.ts; release/package-release.ts |
| replay-test | Test | In Progress | tests/release/cori-alpha-proof.test.ts; tests/release/release-pipeline.test.ts |
| replay-runtime | Runtime | In Progress | src/replay/EglReplay.ts; src/replay/ReplayDriftDetector.ts; src/envelope/EnvelopeValidator.ts |
| replay-conformance | Conformance | In Progress | CIS_CONFORMANCE_SUITE_SPECIFICATION.md; CIS_CONFORMANCE_SUITE_INPUT.spec.json |
| replay-replay | Replay | In Progress | src/replay/EglReplay.ts; src/replay/ReplayDriftDetector.ts; src/envelope/EnvelopeValidator.ts |
| conformance-build | Build | In Progress | release/build-release.ts; release/package-release.ts |
| conformance-test | Test | In Progress | tests/release/cis-conformance-generation.test.ts; tests/release/cori-alpha-proof.test.ts |
| conformance-runtime | Runtime | In Progress | packages/aaes-governance/src/crec.ts; packages/aaes-governance/src/evidenceGraph.ts; tests/release/cis-conformance-generation.test.ts |
| conformance-conformance | Conformance | In Progress | CIS_STANDARDS_TRACEABILITY_MATRIX.md; CIS_CONFORMANCE_SUITE_INPUT.spec.json; CIS_CONFORMANCE_SUITE_SPECIFICATION.md |
| conformance-replay | Replay | In Progress | src/replay/EglReplay.ts; src/replay/ReplayDriftDetector.ts |

## Acceptance Notes

- **Identity**: Identity is canonical, traceable to a CIS requirement, and included in the evidence package.
- **Evidence**: Every evidence artifact is objective, inspectable, and tied to the governing requirement.
- **Constitutional State Record**: The state record identifies the governed decision path and stays auditable.
- **Constitutional Receipt**: The receipt verifies independently and links back to the evidence package.
- **Replay**: Replay reconstructs the governed path without hidden state or private explanation.
- **Conformance**: The conformance result is objective, reproducible, and aligned with the traceability matrix.

## Dashboard Rule

This view is generated from the status companion and should be regenerated rather than edited by hand.

