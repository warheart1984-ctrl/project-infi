# AAES-OS UCR Mapping — TypeScript Monorepo ↔ Python Spine

**Status:** Phase 2 complete; Phase 3+ partially implemented in TypeScript  
**Engineering scope:** Map `aaes-os/packages/*` TypeScript spine to existing Python runtime modules.  
**Canonical Python runtime:** `src/`, `docs/runtime/`, `docs/spine/`

## Summary

| TS package (`aaes-os/packages/`) | Engineering class | Python module | Phase |
|----------------------------------|-------------------|---------------|-------|
| `runledger` | `RunStore` | `src/run_ledger.py` → `RunLedger` | **2** — in-memory API |
| `trace-bus` | `TraceBusClient`, `TraceBus` | `src/aaes_os/trace_bus.py` → `TraceBusValidator` | **2** — pub/sub; validator deferred |
| `aaes-governance` | `InvariantEngine`, `FaultJournal`, `PatternLedger`, `DriftMetrics` | `src/fault_journal.py`, composed runtime invariants | **3+** — v0.1 in TS |
| `ucr-runtime` | `UCRRuntime`, `DefaultUCRRuntime` | `src/ucr/`, `docs/contracts/UCR_ATTESTATION_SPEC.md` | **3** — demo runtime wired |
| `tri-core-protocol` | `PatchLedger`, `PatchProposal`, `ApprovalRecord` | governance policy flows (no 1:1 module yet) | **3** — patch ledger types |

**Scope note:** `@aaes-os/*` is the workspace package scope. Legacy v1 orchestrator remains at `aaes-os/src/`.

## Run ledger

### Python: `RunLedger` (`src/run_ledger.py`)

- Durable JSON file (`.runtime/run-ledger.json`)
- Session-scoped active runs, CISIV lifecycle stages, UL substrate wrapping
- Multi-step Jarvis work history

### TypeScript: `@aaes-os/runledger` → `RunStore`

| Python | TypeScript | Notes |
|--------|------------|-------|
| run creation | `startRun()` | In-memory; optional metadata |
| steps / artifacts | `startSpan()` / `endSpan()` | Span is the Phase 2 step primitive |
| invariant linkage | `linkInvariant(spanId, invariantId)` | Span-scoped link |
| `end_run` | `endRun()` | Rejects open spans → `SPAN_ORPHAN` fault path |

**Remains to unify:** JSON persistence, CISIV stages, UL substrate, session active-run index.

## Trace bus

### Python: `TraceBusValidator` (`src/aaes_os/trace_bus.py`)

- Governed span state machine (`GovernedSpan`)
- Role/auth/hash/causal-order validation (`src/aaes_os/models.py` `TraceEvent`)
- Append-only validated log

### TypeScript: `@aaes-os/trace-bus`

| Python | TypeScript | Notes |
|--------|------------|-------|
| `validate_and_append` | `TraceBusClient.emit()` | Phase 2: pub/sub only |
| structured events | `traceEvents.ts` discriminated unions | `TRACE_SPAN`, `TRACE_FAULT`, etc. |
| helper API | `TraceBus` class | `spanStart`, `runEnd`, convenience emitters |
| local dev sink | `consoleSink()` | stdout subscriber |

**Remains to unify:** `EventType`/`Role` enums, auth envelope, span transitions, hash chain, parity tests with Python validator.

## Fault journal & invariants

### Python: `FaultJournalStore` (`src/fault_journal.py`)

- Append-only `faults.jsonl`
- Fault codes: `INVARIANT_BREACH`, `BRIDGE_BINDING_MISMATCH`, `AUTHORITY_MISMATCH`, `SPAN_ORPHAN`, `RUNTIME_TIMEOUT`
- Spine halt → invariant/fault mapping tables

### TypeScript: `@aaes-os/aaes-governance`

| Python | TypeScript | Notes |
|--------|------------|-------|
| `FaultRecordV1` | `FaultEvent` / `FaultJournal.recordFault()` | Same fault codes in `faultCodes.ts` |
| invariant checks | `InvariantEngine` | Rule modules under `invariants/` |
| pattern recurrence | `PatternLedger` | TS-only v0.1 analytics |
| drift telemetry | `DriftMetrics`, `collectTelemetrySnapshot()` | ops-console integration |

**Remains to unify:** JSONL persistence to `.runtime/fault-journal/faults.jsonl`, spine halt tables from Python, cross-process bridge.

## UCR runtime

### Python / contracts

- `docs/contracts/UCR_ATTESTATION_SPEC.md` — `ucr_register`, attestation token
- `src/ucr/` — kernel registration (when deployed)

### TypeScript: `@aaes-os/ucr-runtime`

| Contract | TypeScript | Notes |
|----------|------------|-------|
| governed execution shell | `UCRRuntime.run()` | `DefaultUCRRuntime` wires store + bus + governance |
| span orphan guard | `withSpanGuard()` | Maps to `SPAN_ORPHAN` |
| output normalization | `outputPatches.ts` | demo patch hooks |
| minimal stub | `StubUCRRuntime` | happy-path only |

**Remains to unify:** attestation token types, `ucr_register` refusal codes, Python custody handle.

## Tri-Core — two distinct concepts

### 1. Governance triad protocol (`tri-core-protocol` package)

Engineering: `TriCoreRole`, `PatchProposal`, `ApprovalRecord`, `PatchLedger`.

Purpose: proposer / reviewer / approver workflow for governed patches.

**Python equivalent:** no dedicated module; closest is `.runtime/governance/policy-requests.json`.

### 2. Nova Face thalamus binding (`tri_core` in `nova_face.py`)

```python
TRI_CORE_AUTHORITY = "tri_core"
bridge_nova_face_to_cortex_and_tri_core(...)
```

Purpose: companion-surface routing authority lane — **not** the triad patch protocol.

| Concept | Location | Do not conflate |
|---------|----------|-----------------|
| Triad patch protocol | `packages/tri-core-protocol` | Governance approvals |
| Thalamus `tri_core` lane | `src/cog_runtime/nova_face.py` | Cognitive routing |

## Legacy TypeScript orchestrator (`aaes-os/src/`)

Pre-monorepo AAES-OS v1:

- `AAESOrchestrator`, pipeline engines, `InMemoryTraceStore`
- HTTP server on `:8080`

**Relationship:** application layer above spine packages. Future services should depend on `@aaes-os/runledger` + `@aaes-os/trace-bus`.

## Services & placeholders

| Path | Purpose | Status |
|------|---------|--------|
| `services/ops-console/` | Telemetry / patch ops HTTP UI | v0.1 implemented |
| `infra/` | Deploy manifests | placeholder |
| `tools/` | drift-demo, telemetry-cli, patch demos | scripts present |

## Build order (Phases 1–5)

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | pnpm workspace, package shells, branded IDs | Done |
| 2 | `RunStore`, `TraceBusClient`, integration tests | Done |
| 3 | governance + UCR + tri-core | v0.1 TS implementation |
| 4 | `services/` facades | `ops-console` started |
| 5 | `infra/` persistence / k8s | Placeholder |

## Integration tests

| Test | Path | Flow |
|------|------|------|
| Run/trace wire | `tests/integration/run-trace-flow.test.ts` | startRun → span → invariant trace → end |
| Fault wire | `tests/integration/v01-wire.test.ts` | invariant breach → `FaultJournal` → `TRACE_FAULT` |
| Invariant engine | `tests/integration/invariant-engine.test.ts` | `UCRRuntime` + governance |

## Next steps

1. **Persistence adapters** — JSONL fault journal + run ledger file parity with Python paths.
2. **Trace validator port** — `TraceBusValidator` rules from `src/aaes_os/trace_bus.py`.
3. **UCR attestation** — token/register types from `UCR_ATTESTATION_SPEC.md`.
4. **Cross-language bridge** — shared event schema for Python composed runtime → TS trace bus.
5. **Infra** — durable stores, observability exporters under `infra/`.

## Evidence

- **Claim:** Phase 2 spine implemented; mapping documented.  
- **Validation:** `pnpm install && pnpm test` from `aaes-os/`.  
- **Provenance:** `aaes-os/packages/*`, `aaes-os/tests/integration/`.
