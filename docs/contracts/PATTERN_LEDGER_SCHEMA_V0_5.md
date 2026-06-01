# Unified Pattern Ledger Schema v0.5

Status: **Phase 1 admitted** — canonical cross-surface ledger contract.

Authority: `docs/contracts/COLLECTIVE_PATTERN_LEDGER.md`, `docs/contracts/UGR_RUNTIME_CONTRACT.md`.

Machine schema: `docs/contracts/pattern-ledger-schema-v0.5.json`

## Purpose

One governed ledger shape for:

- AAIS detachment guard pattern events
- UGR convergence claims and evidence
- Wolf CoG cogos pattern rows (via adapter normalization)

Local truth remains authoritative. Collective sharing stays signature-only per Collective Pattern Ledger law.

## Storage Layout

Under `AAIS_RUNTIME_DIR` (default `.runtime/`):

```text
collective-pattern-ledger/
  unified/
    claims.jsonl
    evidence.jsonl
    provenance.jsonl
    pattern_events.jsonl
  detachment-patterns.jsonl   # legacy mirror for backward compatibility
```

Implementation: `src/ugr/unified_pattern_ledger.py`

## Record Types

| Type | Purpose |
|---|---|
| `claim` | Structured belief from lanes or convergence |
| `evidence` | Source artifact with classification |
| `provenance_link` | Links claims/events to evidence |
| `pattern_event` | Fame/shame/detachment/cogos-style events |

All records require:

- `record_type`
- `ledger_version`: `"0.5"`
- `timestamp` (UTC ISO-8601)

## Claim Fields

- `claim_id`, `subject`, `predicate`, `object`
- `confidence` (0–1)
- `source_lane`
- `status`: `proposed | accepted | rejected | contested`
- `tenant_scope`: `global | tenant:<id>`
- `evidence_refs[]`

## Provenance Link Fields

- `provenance_id`
- `node_or_edge_id` (claim_id or pattern_id)
- `evidence_id`
- `support_type`: `supports | contradicts | refines`
- `weight` (0–1)

## Wolf CoG Adapter

`normalize_cogos_pattern_record()` maps cogos daemon rows into `pattern_event` records with `origin: cogos`.

Ingestion is read-normalize-write; cogos runtime code is not modified in Phase 1.

## Invariants

1. Append-only writes — no silent mutation of prior records
2. Provenance required before a claim may be promoted to `accepted` in UGR convergence path
3. Tenant-scoped records never appear in another tenant's query results
4. Signature-only export — no raw prompts, traces, or reconstructable private content in shared fields

## Verification

```bash
py -3.12 -m pytest tests/test_unified_pattern_ledger.py tests/test_ugr_runtime.py -q
```
