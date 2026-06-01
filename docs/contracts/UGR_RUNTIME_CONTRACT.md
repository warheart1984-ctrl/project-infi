# UGR Runtime Contract (UGR-RC-01)

Status: **Phase 1 admitted** — bridge invariant gate + unified ledger v0.5.

Authority: `META_ARCHITECT_LAWBOOK.md`, `docs/contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md`,
`docs/contracts/COLLECTIVE_PATTERN_LEDGER.md`.

## Definition

The Unified Governed Runtime (UGR) is the cloud-scale orchestration layer that:

- receives deliberation and analysis requests under Jarvis authority
- spawns governed parallel reasoning lanes (MLCA)
- merges lane outputs through a deterministic Convergence Engine
- reads and writes the Pattern Ledger under invariant checks
- emits full audit traces

UGR extends the Cognitive Bridge; it does not replace it.

## Core Law

1. **Bridge first** — no UGR request executes without a cleared Cognitive Bridge decision.
2. **Lanes are guests** — lanes propose structured claims; they do not mutate global state directly.
3. **Convergence is judge** — only Convergence Engine output becomes UGR belief or plan.
4. **Deterministic merge** — convergence rules are versioned and reproducible.
5. **Trace everything** — every request carries a `trace_id` linking bridge, lanes, and merge.

## Lane Types (v0 palette)

| Type | Role | May execute tools | May mutate ledger |
|---|---|---|---|
| `symbolic` | Invariant and constraint checks | no | no |
| `graph` | Pattern ledger queries | no | no |
| `llm` | Generative hypothesis (proposal-only) | no | no |
| `simulation` | Bounded scenario projection | no | no |

## Convergence Precedence (v0)

When lanes conflict on the same claim subject+predicate:

1. Hard invariant failure → reject claim
2. `symbolic` accepted > `graph` accepted > `llm` accepted
3. Multi-lane consensus increases confidence
4. Unresolved conflict → `contested` status + human review flag

## Pattern Ledger Extension (v0.5)

UGR adds structured `claims[]` on top of Collective Pattern Ledger law:

```json
{
  "claim_id": "string",
  "subject": "string",
  "predicate": "string",
  "object": "string",
  "confidence": 0.0,
  "source_lane": "symbolic | graph | llm | simulation",
  "evidence_refs": ["string"],
  "tenant_scope": "global | tenant:<id>",
  "status": "proposed | accepted | rejected | contested"
}
```

Ledger storage uses unified v0.5 JSONL under `collective-pattern-ledger/unified/` (see `docs/contracts/PATTERN_LEDGER_SCHEMA_V0_5.md`).

## API Contract

### `POST /api/ugr/deliberate`

Request:

```json
{
  "question": "string",
  "intent": "diagnose_runtime | governance_review | general_qa",
  "tenant_id": "default",
  "context": {},
  "lane_types": ["symbolic", "graph", "llm"]
}
```

Response:

```json
{
  "trace_id": "string",
  "bridge": {},
  "lane_results": [],
  "convergence": {},
  "summary": "string"
}
```

## Module Map

| Module | Path |
|---|---|
| Unified runtime | `src/ugr/unified_runtime.py` |
| Lane manager | `src/ugr/lane_manager.py` |
| Convergence engine | `src/ugr/convergence_engine.py` |
| Pattern ledger store | `src/ugr/pattern_ledger.py` |

## Failure Rule

Missing bridge clearance, unknown lane type, convergence error, or trace write failure →
fail closed with structured error and no accepted beliefs.
