# AAES-OS Governed Memory (Tri-Strata) — Engineering Contract

**Mythic (docs only):** Governed Cognitive Substrate / AAES Triangle  
**Engineering:** `IntentLedger`, `AuthorityLedger`, `ExecutionMemory`, `GovernanceEnforcementEngine`

## Purpose

Three memory strata prevent hallucinated goals, unauthorized actions, untraceable reasoning, and silent drift:

| Stratum | Question | Writer | Persistence | Failure |
|---------|----------|--------|-------------|---------|
| Intent Memory | Why? | Operator / governance only | Append-only ledger | `INTENT_DRIFT` |
| Authority Memory | Allowed? | Governance | Semi-permanent tokens | `AUTHORITY_FAULT` |
| Execution Memory | Doing what now? | Runtime (ephemeral) | In-process only | `EXECUTION_FAULT` |

**Invariant:** Execution → Authority → Intent (narrowing chain).

## Implemented (v0.1 scaffold + vertical slice)

| Component | TypeScript | Python |
|-----------|------------|--------|
| Types | `aaes-os/packages/governed-memory/src/types.ts` | `governed_memory/types.py` |
| Intent ledger | `intentLedger.ts` | `intent_ledger.py` |
| Authority ledger | `authorityLedger.ts` | `authority_ledger.py` |
| Execution memory | `executionMemory.ts` | `execution_memory.py` |
| Governance engine | `governanceEnforcement.ts` | `governance_enforcement.py` |
| Operator façades | `facade.ts` (`createIntent`, `issueAuthority`, …) | `governed_memory/facade.py` |
| Deterministic replay | `replay.ts` | `governed_memory/replay.py` |
| Core re-exports | `aaes-os/core/**` | `governed_memory` (canonical) |

**Tests:** `governedMemory.test.ts`, `verticalSlice.test.ts`, `tests/test_governed_memory_tri_strata.py`, `tests/test_governed_memory_vertical_slice.py`

### Replay protocol (governance-only)

`replay(span_id)` re-validates stored traces against intent chain integrity, authority binding (token exists, not revoked, intent version match), and per-step justification. It does **not** re-execute LLM or tool side effects.

### Layout

Implementation lives in `aaes-os/packages/governed-memory` and `governed_memory/`. Thin shims under `aaes-os/core/` re-export façades for the plan’s folder layout without duplicating logic.

## Not yet implemented (follow-up)

- Cryptographic signatures on `IntentRecord` / `AuthorityEnvelope` (stubs use `sig:` prefixes)
- Full Merkle-chained intent ledger (hash chain is structural placeholder)
- Pattern Ledger, NexusOS integration layer
- Full Ultima planner/reasoner loop
- `InvariantEngine.rejectOnViolation` halt semantics (see `aaes-os/packages/aaes-governance`)
- L2 corridor envelope adjudication, L3 immune quarantine in loader

## Relation to Runtime Law Spine (RLS)

| Tri-Strata | RLS |
|------------|-----|
| Intent Memory | Intent ledger / operator goals |
| Authority Memory | Corridor envelopes, capability tokens, `AuthorityEnvelope` |
| Execution Memory | Spans, traces, `runledger` |
| Governance Enforcement | `RuntimeLawSpineGate`, `InvariantEngine`, immune quarantine |

Entrypoints (`aais/launcher.py`, `operator_kernel/main.py`) call `RuntimeLawSpineGate.require_sealed()` when `RLS_STRICT=1`.

## Relation to TriCoreRole

**Do not conflate:** `TriCoreRole` (ARCHITECTURE / GOVERNANCE / EXECUTION) in `aaes-os` is a *runtime role* split. Tri-Strata is a *memory governance* model. They compose but are not aliases.

## Failure modes

- **Intent fault:** drift vs active intent version → halt span, require operator re-sign
- **Authority fault:** expired/revoked token → terminate span
- **Execution fault:** missing trace justification → kill span, optional checkpoint replay

Canonical fault codes: `INTENT_DRIFT`, `AUTHORITY_FAULT`, `EXECUTION_FAULT`, `LEDGER_INTEGRITY`.
