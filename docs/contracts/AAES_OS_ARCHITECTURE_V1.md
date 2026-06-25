# AAES-OS Architecture v1 — Coding-Agent Contract

Status: **active companion** to [AAES_OS_V1_FORMAL_SPEC.md](./AAES_OS_V1_FORMAL_SPEC.md)

Mythic label: **AAES-OS** (Adaptive Autonomous Execution Substrate).

Engineering package: `src/aaes_os/`.

## 1. Purpose

This document reconciles the concise cognitive-agent architecture rundown with the normative RFC v1.0 governed-span trace layer. Coding agents MUST treat:

- **Trace Bus** (`TraceBusValidator`) as the governance spine for span lifecycle
- **GovernedSpan** as the request lifecycle handle
- **CognitiveOrchestrator** as the stub cognitive runtime that emits pipeline steps and trace events

Precedence: Law → Blueprint → Contract → Implementation. The formal spec wins on trace semantics; this doc wins on module boundaries and MVP phasing.

## 2. Four layers

| Layer | Engineering surface | Responsibility |
|-------|---------------------|----------------|
| **Interface** | `src/aaes_os/api.py`, `app/main.py` router mount | HTTP `/aaes/execute`, `/aaes/trace/{trace_id}` |
| **Cognitive Runtime** | `CognitiveOrchestrator`, `UnifiedLinguisticSurface`, `modules/daniel.py` | Perception → explain pipeline; pluggable execution |
| **Governance & Invariants** | `InvariantEngine`, `PolicyEngine`, `TraceBusValidator`, `GovernedSpan` | Pre/post checks; allow/block/warn; span state machine |
| **Persistence & Integration** | `TraceStore`, future `operator_decision_ledger` bridge | Append-only trace records; domain ledger remains separate |

## 2.1 Continuity-native OS stack

AAES-OS v1 also participates in the continuity-native stack:

```
+------------------------------+
| Identity Kernel (ICK)        |
+------------------------------+
| Computational Kernel (CCK)   |
+------------------------------+
| Continuity Substrate (CS)    |
+------------------------------+
| Wave Math Engine (WMMS-1)    |
+------------------------------+
| Cross-Kernel Coherence (CKCE)|
+------------------------------+
| Federation Engine (FCP-1)    |
+------------------------------+
| Execution Layer (AAES)       |
+------------------------------+
```

The execution layer enforces CEC-1 for continuity-typed DAR-Z handoffs through
`src/aaes_os/continuity_execution.py`.

## 3. Pipeline stages

| Stage | Engineering enum | Emits TraceEvent | Typical span state after |
|-------|------------------|------------------|--------------------------|
| Perception | `AAESStepType.PERCEPTION` | *(aggregated into INTENT)* | `INIT` → `INTENTED` |
| Deliberation | `AAESStepType.DELIBERATION` | *(aggregated into INTENT)* | `INTENTED` |
| Planning | `AAESStepType.PLANNING` | *(feeds DECISION payload)* | `INTENTED` → `DECIDED` |
| Action | `AAESStepType.ACTION` | `EXECUTION` | `DECIDED` → `EXECUTING` |
| Explain | `AAESStepType.EXPLAIN` | `RESULT` | `EXECUTING` → `RESULTED` → `CLOSED` |

Orchestrator stub batches perception + deliberation into a single `INTENT`, planning into `DECISION`, action into `EXECUTION`, explain into `RESULT`.

## 4. Core types

| Type | Module | Role |
|------|--------|------|
| `AAESRequest` | `pipeline_types.py` | Inbound operator/agent request |
| `AAESContext` | `pipeline_types.py` | Mutable per-request execution context |
| `AAESStep` | `pipeline_types.py` | One pipeline stage observation |
| `AAESDecision` | `pipeline_types.py` | Policy/governor verdict before execution |
| `AAESAction` | `pipeline_types.py` | Bounded module invocation descriptor |
| `TraceEvent` | `models.py` | Normative governed-span event (RFC) |
| `GovernedSpan` | `governed_span.py` | Span state machine handle |

## 5. Module contracts

### 5.1 UnifiedLinguisticSurface (`uls.py`)

| Function | Inputs | Outputs | Failure modes |
|----------|--------|---------|---------------|
| `normalize_input(raw)` | `str` | normalized `str` | empty → `ValueError` |
| `semantic_compare(left, right)` | two `str` | `float` 0..1 | invalid type → `TypeError` |
| `summarize_trace(steps, events?)` | `list[AAESStep]`, optional events | summary `str` | invalid steps → `TypeError` |

### 5.2 InvariantEngine (`invariant_engine.py`)

| Function | Inputs | Outputs | Failure modes |
|----------|--------|---------|---------------|
| `check(...)` | request, runtime_context, optional steps/event | `InvariantCheckResult` | — |
| `check_or_raise(...)` | same | result or raise | `AaesOsValidationError` |

### 5.3 PolicyEngine (`policy_engine.py`)

| Function | Inputs | Outputs | Failure modes |
|----------|--------|---------|---------------|
| `evaluate(request, context?)` | `AAESRequest`, optional `AAESContext` | `AAESDecision` with `allow` / `block` / `warn` | invalid request → `ValueError` |

Block code at HTTP layer: `AAES_POLICY_BLOCKED`.

### 5.4 DanielExecutionModule (`modules/daniel.py`)

| Function | Inputs | Outputs | Failure modes |
|----------|--------|---------|---------------|
| `execute(action)` | `AAESAction` | `dict` stub outcome | unknown module → `KeyError` |
| `ModuleRegistry.execute(action)` | `AAESAction` | module outcome | same |

### 5.5 TraceStore (`trace_store.py`)

| Function | Inputs | Outputs | Failure modes |
|----------|--------|---------|---------------|
| `save_execute_result(result, bus?)` | `AAESExecuteResult` | — | wrong type → `TypeError` |
| `get(trace_id)` | `str` | record or `None` | empty id → `ValueError` |

### 5.6 CognitiveOrchestrator (`orchestrator.py`)

| Function | Inputs | Outputs | Failure modes |
|----------|--------|---------|---------------|
| `execute(request)` | `AAESRequest` | `AAESExecuteResult` | invariant/policy block → blocked result; bus reject → `block_code` from `AaesOsValidationError` |

## 6. Seven Invariants ↔ RFC INV-1..7 ↔ InvariantEngine

| # | Architecture invariant | RFC id(s) | InvariantEngine check |
|---|------------------------|-----------|------------------------|
| 1 | Traceability | INV-1, INV-2 | Auth + hash via `TraceBusValidator`; parent links on append |
| 2 | Integrity of State | INV-3, INV-5 | Causal order + `runtime_context` consistency in bus |
| 3 | Identity & Auth | INV-1 | `AuthEnvelope.validate()` in preflight and bus |
| 4 | Scope & Boundaries | INV-7 | `PolicyEngine` deny list; `EXECUTION` requires `DECISION` in bus |
| 5 | Explainability Hook | INV-6 (payload) | Post-action: `explain` step required; `RESULT` carries `explanation` |
| 6 | Reversibility / Failsafe | INV-6 | `RESULT.payload.rollback_possible` required before append |
| 7 | Governance First | INV-7 | Policy block before span events; no `EXECUTION` without `DECISION` |

## 7. AAESStep ↔ TraceEvent ↔ Span state

| AAESStepType | TraceEvent type | Span transition |
|--------------|-----------------|-----------------|
| `perception` | — (rolled into `INTENT`) | — |
| `deliberation` | — (rolled into `INTENT`) | `INIT` → `INTENTED` on `INTENT` |
| `planning` | — (rolled into `DECISION`) | `INTENTED` → `DECIDED` on `DECISION` |
| `action` | `EXECUTION` | `DECIDED` → `EXECUTING` |
| `explain` | `RESULT` | `EXECUTING` → `RESULTED`; close → `CLOSED` |

## 8. How `aaes_os` fits

```
AAESRequest
    → CognitiveOrchestrator.execute()
        → InvariantEngine (preflight)
        → CEC-1 continuity execution preflight (when DAR-Z handoff is present)
        → ULS.normalize_input
        → PolicyEngine.evaluate
        → GovernedSpan + TraceBusValidator (INTENT→DECISION→EXECUTION→RESULT)
        → ModuleRegistry / DanielExecutionModule
        → TraceStore.save_execute_result
```

- **Trace Bus** = governance spine (append-only, invariant enforcement)
- **Spans** = one request lifecycle (`trace_id` correlates store; `span_id` correlates bus)
- **Operator Decision Ledger** (`src/operator_decision_ledger.py`) = separate accountability graph; future bridge MAY ingest `DECISION` events

## 9. MVP phase checklist

### Phase 1 — Skeleton (current)

| Item | Path | Status |
|------|------|--------|
| Pipeline types | `src/aaes_os/pipeline_types.py` | implemented |
| Orchestrator stubs | `src/aaes_os/orchestrator.py` | implemented |
| HTTP `/aaes/execute` | `src/aaes_os/api.py`, `app/main.py` | implemented |
| Trace store | `src/aaes_os/trace_store.py` | in-memory + optional JSONL |

### Phase 2 — Governance engines

| Item | Path | Status |
|------|------|--------|
| InvariantEngine | `src/aaes_os/invariant_engine.py` | basic mapping + pre/post checks |
| PolicyEngine | `src/aaes_os/policy_engine.py` | allow/block/warn + deny list |

### Phase 3 — ULS + Daniel

| Item | Path | Status |
|------|------|--------|
| ULS stub | `src/aaes_os/uls.py` | normalize + summarize; semantic_compare token overlap |
| Daniel module | `src/aaes_os/modules/daniel.py` | stub execute + registry |

### Phase 4 — Failsafe + trace retrieval

| Item | Path | Status |
|------|------|--------|
| Rollback flag on RESULT | `orchestrator.py` + bus INV-6 | implemented |
| GET `/aaes/trace/{trace_id}` | `src/aaes_os/api.py` | implemented |
| SQLite / ledger bridge | — | **stub / not started** |

### Phase 5 — Continuity execution

| Item | Path | Status |
|------|------|--------|
| CKCE-1 theorem enforcement | `src/continuity/ckce.py` | implemented |
| CEC-1 preflight and propagation | `src/aaes_os/continuity_execution.py` | implemented |
| DAR-Z substrate fields on AAES events | `src/aaes_os/orchestrator.py` | implemented |

## 10. Tests

| Suite | Path |
|-------|------|
| RFC v1 trace bus | `tests/test_aaes_os_v1.py` |
| Architecture orchestrator | `tests/test_aaes_os_architecture.py` |
| CKCE-1 coupling theorem | `tests/test_cross_kernel_coherence_engine.py` |
| CEC-1 continuity execution | `tests/test_aaes_continuity_execution_contract.py` |

## 11. Version

- Architecture: `aaes_os.architecture.v1`
- Formal spec: `aaes_os.v1.0`
- Module id: `AAIS-AAES-OS-01`
