# Evidence Receipt Model

Status: **active normative model**

Engineering contract: `EvidenceReceiptModel`

Canonical proof law: [REPO_PROOF_LAW.md](../../REPO_PROOF_LAW.md) — *if it is not proven, it is not complete.*

## Trust chain

**Claim → Evidence → Verification → Acceptance**

Fluency and model confidence are not evidence. Each claim that affects governed behavior must bind to at least one typed receipt.

## Five receipt classes

| Class | Engineering type | What it proves | Primary anchors in repo |
|-------|------------------|----------------|-------------------------|
| **Decision** | `OperatorDecisionReceipt` | Who decided what, under which authority | `src/operator_decision_ledger.py` (`brain_decision`, `urg_receipt`, etc.) |
| **Execution** | `ExecutionStageReceipt` | What ran, with what inputs/outputs | D3 kernel ledger, OTEM stages, `src/run_ledger.py` |
| **Validation** | `ValidationProofReceipt` | Independent check passed | Trust Bundles (`docs/TRUST_BUNDLE_SPEC.md`), pytest artifacts, gate logs |
| **Provenance** | `ProvenanceAttestationReceipt` | Origin, signing, admission path | USL signing, bridge attestation, mission receipts |
| **Temporal** | `TemporalReplayReceipt` | Replayable timeline for audit | `src/temporal_replay/`, UGR mission receipt store |

## Required fields (minimum)

Every receipt SHOULD include:

| Field | Type | Notes |
|-------|------|-------|
| `receipt_id` | string | Stable unique id |
| `receipt_class` | enum | One of the five classes above |
| `claim_label` | string | Links to the claim being supported |
| `timestamp_utc` | ISO-8601 | Event time |
| `actor` | string | Human, agent, or subsystem id |
| `authority_boundary` | string | What this receipt does *not* authorize |
| `artifact_refs` | string[] | Paths, bundle ids, or content hashes |

Nova lawful productization adds chain fields (`identity`, `trace`, `reproducibility`) — see [NOVA_LAWFUL_PRODUCTIZATION.md](../runtime/NOVA_LAWFUL_PRODUCTIZATION.md).

## Bidirectional linking

Per [REPO_PROOF_LAW.md](../../REPO_PROOF_LAW.md):

1. Every **claim** in a PR, trust bundle, or manifest lists `evidence_refs[]`.
2. Every **receipt** lists `claim_label` (or `claim_labels[]`).
3. Orphan receipts without claims are audit-only, not completion proof.

## Mapping to existing artifacts

| Artifact | Receipt classes typically present |
|----------|-----------------------------------|
| Agent Safety manifest | Decision, Validation, Provenance |
| Trust Bundle (Doctrine XI) | Validation, Provenance |
| Proof bundle template | Validation, Execution |
| Operator ledger events | Decision, Temporal |
| AAES-OS trace events (`src/aaes_os/`) | Decision, Execution, Temporal, Provenance |
| CI workflow logs | Validation |

## Failure modes

| Condition | Response |
|-----------|----------|
| Claim without receipt | Not complete; block merge or mark `asserted` only |
| Receipt without claim | Audit artifact only |
| Conflicting receipts | Escalate; Swarm Law hold |
