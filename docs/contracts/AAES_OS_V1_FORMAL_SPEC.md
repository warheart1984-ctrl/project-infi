# AAES-OS v1.0 Formal Specification

Status: **active contract** (Standards Track, Draft for Implementation)

Mythic label: **AAES-OS** (Adaptive Autonomous Execution Substrate — Operating System trace layer).

Engineering module: `src/aaes_os/` (`GovernedSpanEngine`, `TraceBusValidator`, `RuntimeContextRecord`).

Canonical law precedence: [META_ARCHITECT_LAWBOOK.md](../../META_ARCHITECT_LAWBOOK.md) — Law → Blueprint → Contract → Implementation.

## 1. Scope

This contract defines the normative governed-span trace model for AAIS standalone product admission. It specifies:

- span lifecycle and state machine
- trace event schema and causal chain
- authority roles and allowed emissions
- trace bus validation and append-only log semantics
- runtime context binding for deterministic reconstruction

Implementation reference: `src/aaes_os/`. Non-normative TS/Rust sketches live under `reference/aaes_os_v1/`; see [AAES_OS_INTERFACE_V1.md](./AAES_OS_INTERFACE_V1.md).

## 2. Governed span lifecycle

### 2.1 Span states

| State | Meaning |
|-------|---------|
| `INIT` | Span allocated; no governed events yet |
| `INTENTED` | Intent recorded under authority |
| `DECIDED` | Governor decision recorded |
| `EXECUTING` | Executor began bounded work |
| `RESULTED` | Result recorded |
| `CLOSED` | Span sealed; no further events |

### 2.2 Legal transitions (§5.2)

| From | Event type | To |
|------|------------|-----|
| `INIT` | `INTENT` | `INTENTED` |
| `INTENTED` | `DECISION` | `DECIDED` |
| `DECIDED` | `EXECUTION` | `EXECUTING` |
| `EXECUTING` | `RESULT` | `RESULTED` |
| `RESULTED` | *(close)* | `CLOSED` |

Illegal transitions MUST be rejected by the trace bus with reason code `AAES_SPAN_STATE_INVALID`.

## 3. Event types and causal chain

### 3.1 Event types

| Type | Engineering enum | Typical emitter role |
|------|------------------|----------------------|
| Intent | `INTENT` | `USER`, `RUNTIME` |
| Decision | `DECISION` | `GOVERNOR` |
| Execution | `EXECUTION` | `EXECUTOR` |
| Result | `RESULT` | `EXECUTOR` |

### 3.2 Causal chain (INV-3)

Within a span, the first emission of each type MUST appear in order:

`INTENT` → `DECISION` → `EXECUTION` → `RESULT`

Each non-intent event SHOULD set `parent_event_id` to the immediately preceding causal event in the span.

## 4. TraceEvent schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `event_id` | string | yes | Stable unique id |
| `span_id` | string | yes | Governed span id |
| `event_type` | enum | yes | One of §3.1 |
| `timestamp_utc` | ISO-8601 | yes | Event time |
| `auth` | AuthEnvelope | yes | §4.1 |
| `runtime_context` | RuntimeContext | yes | §5 |
| `payload` | object | yes | Bounded action data |
| `parent_event_id` | string \| null | no | Causal parent event |
| `parent_span_id` | string \| null | no | Upstream span link |
| `event_hash` | string | yes | Content digest (§4.2) |

### 4.1 AuthEnvelope

| Field | Type | Required |
|-------|------|----------|
| `role` | Role enum | yes |
| `actor_id` | string | yes |
| `signature_hash` | string | yes | Authenticity binding |

### 4.2 event_hash

`event_hash` MUST equal SHA-256 (hex) of canonical JSON of the event record **excluding** `event_hash`, with sorted keys and compact separators.

## 5. RuntimeContext

| Field | Type | Required |
|-------|------|----------|
| `runtime_version` | string | yes |
| `invariant_version` | string | yes |
| `prompt_hash` | string | yes |
| `decision_policy_hash` | string | yes |
| `toolchain_hash` | string | yes |
| `memory_snapshot_hash` | string | yes |

All hashes MUST be non-empty for admission. Missing fields fail with `AAES_RUNTIME_CONTEXT_INVALID`.

## 6. Authority model

| Role | May emit | MUST NOT emit |
|------|----------|---------------|
| `USER` | `INTENT` | `DECISION`, `EXECUTION`, `RESULT` |
| `RUNTIME` | `INTENT` | `DECISION`, `EXECUTION`, `RESULT` |
| `GOVERNOR` | `DECISION` | `INTENT`, `EXECUTION`, `RESULT` |
| `EXECUTOR` | `EXECUTION`, `RESULT` | `INTENT`, `DECISION` |
| `OBSERVER` | *(none)* | all write events |

Violations MUST fail with `AAES_AUTH_ROLE_DENIED`.

## 7. Invariants

| Id | Name | Rule |
|----|------|------|
| INV-1 | Authenticity | Every event carries a valid `AuthEnvelope` (`actor_id`, `role`, `signature_hash` non-empty) |
| INV-2 | Traceability | `event_hash` matches payload; `parent_event_id` references an event already in the bus for this span |
| INV-3 | Causal completeness | Event types follow §3.2 order; no skipped stage |
| INV-4 | Reconstructability | `RuntimeContext` present and stable for all events in a span |
| INV-5 | Identity consistency | `runtime_context` field values are identical across all events in a span |
| INV-6 | Rollback possibility | `RESULT` payload SHOULD include `rollback_possible: bool` |
| INV-7 | Constitutional execution | `EXECUTION` MUST NOT be admitted unless a `DECISION` event exists in the span |

## 8. Trace bus

Engineering class: `TraceBusValidator`.

Responsibilities:

1. Validate event schema, auth, runtime context, and invariants INV-1..INV-7
2. Validate span state transition table (§2.2)
3. Append to immutable in-memory log (production may persist via bridge)
4. Reject illegal transitions with structured reason codes

Public surface:

- `validate_and_append(event, span)` → appended event
- `events_for_span(span_id)` → ordered list
- `reject_reason` on `AaesOsValidationError`

## 9. governedAction protocol

Engineering helper: `governed_action()`.

Sequence:

1. **Pre-validate** — allocate span in `INIT`; validate and append `INTENT`
2. **Decide** — caller supplies decision payload; append `DECISION`
3. **Execute** — run bounded callable; append `EXECUTION` then work
4. **Result** — append `RESULT` with outcome payload
5. **Close** — transition span to `CLOSED`

Any validation failure MUST abort before side effects when failure occurs at pre-validate or decide stages.

## 10. Reconstruction protocol

Engineering function: `reconstruct_span(bus, span_id)`.

MUST be deterministic: given the same append-only log, reconstruction yields the same `ReconstructedSpan` record.

Reconstruction validates:

- causal chain INV-3
- parent links INV-2
- terminal state (`CLOSED` preferred; `RESULTED` acceptable for open spans)

Failure raises `AaesOsValidationError` with code `AAES_RECONSTRUCT_FAILED`.

## 11. Mapping to existing AAIS modules

| RFC concept | Existing module | Relationship |
|-------------|-----------------|--------------|
| Decision receipts | `src/operator_decision_ledger.py` | Domain-specific decision graph; MAY ingest AAES `DECISION` events via future bridge |
| Temporal replay | `src/temporal_replay/` | Replay envelope for cross-subsystem timelines |
| Safety envelope | `src/safety_envelope.py` | Halt signal; orthogonal to span trace |
| UGR ledger bridge | `src/ugr/ledger_bridge/` | Claim traverse invariants; complementary boundary |
| Scorpion TraceEvent | `scorpion/events.py` | Host telemetry domain; not governed-span semantics |

AAES-OS is the **span primitive**; operator decision ledger remains the **operator accountability graph**. Do not duplicate ledger persistence in v1 reference.

## 12. Evidence receipt mapping

Per [EVIDENCE_RECEIPT_MODEL.md](../governance/EVIDENCE_RECEIPT_MODEL.md):

| Receipt class | AAES-OS binding |
|---------------|-----------------|
| **Decision** | `DECISION` events with `auth.role=GOVERNOR` |
| **Execution** | `EXECUTION` events |
| **Validation** | Trace bus rejection logs; pytest `tests/test_aaes_os_v1.py` |
| **Provenance** | `AuthEnvelope.signature_hash`, `RuntimeContext.toolchain_hash` |
| **Temporal** | Ordered append-only bus + `reconstruct_span()` |

Each receipt SHOULD carry `claim_label` and `evidence_refs[]` when promoted to trust bundles.

## 13. Failure reason codes

| Code | Meaning |
|------|---------|
| `AAES_AUTH_MISSING` | Auth envelope incomplete |
| `AAES_AUTH_ROLE_DENIED` | Role cannot emit event type |
| `AAES_SPAN_STATE_INVALID` | Illegal span transition |
| `AAES_CAUSAL_VIOLATION` | INV-3 ordering breach |
| `AAES_PARENT_MISSING` | parent_event_id not in log |
| `AAES_HASH_MISMATCH` | event_hash does not match body |
| `AAES_RUNTIME_CONTEXT_INVALID` | RuntimeContext incomplete |
| `AAES_IDENTITY_DRIFT` | INV-5 runtime_context mismatch |
| `AAES_RECONSTRUCT_FAILED` | Deterministic rebuild failed |

## 14. Version

- Spec: `aaes_os.v1.0`
- Invariant set: `aaes_os_invariants.v1`
- Reference implementation module id: `AAIS-AAES-OS-01`
