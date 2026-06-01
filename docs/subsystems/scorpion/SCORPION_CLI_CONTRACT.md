# Scorpion CLI Contract

## Status

Stage: 1–4 runtime scaffold  
Claim: `asserted` for native eBPF / Wolf live ingest, `proven` for local fixture+audit+CI evidence.

Runtime entrypoint: `py -3.12 -m scorpion.scorpion`  
Implementation file: `scorpion/scorpion.py`  
Focused tests: `tests/test_scorpion.py`

## Contract Intent

Define a safe command surface for OS anomaly extraction with dry-run defaults
and explicit mode gating.

## Command Set

### `scorpion observe`

Read-only summary of scope, invariant catalog coverage, and trace path.

Required: `--case-id <id>`  
Optional: `--scope`, `--trace-path`, `--goal`

### `scorpion ingest`

Load and normalize trace events from fixture or NDJSON stream.

Required: `--case-id`, `--trace-path`

### `scorpion scan`

Run invariant evaluators; emit drift candidates.

Required: `--case-id`, `--trace-path`

### `scorpion judge`

Gate approve/reject on anomaly claim. Approve requires `--allow-approve` and `--reviewer`.

Required: `--case-id`, `--decision`, `--reviewer` (for approve)

### `scorpion extract`

Sandbox anomaly bundle under temp replay chamber (no host mutation).

Required: `--case-id`, `--trace-path`

### `scorpion reconstruct`

Emit deterministic reconstruction plan JSON (dry-run only).

Required: `--case-id`, `--trace-path`

### `scorpion report` / `snapshot` / `snapshot-index`

Hash-linked proof chain (non-destructive).

### `scorpion status`

Stage posture summary (1–4 claim labels, traceability).

### `scorpion snapshot-query`

Filter append-only snapshot index by `--snapshot-id` / `--case-id`.

### `scorpion trace-query` / `reconcile-query` / `drift-window-query`

Read-only governance queries (Stage 2).

### `--sentinel`

`fixture` (default), `audit` (NDJSON or audit text export), `kernel` (NDJSON bridge; native capture asserted).

### `scorpion verify` / `chaos-check` / `bundle-export`

CI-read-only governance exports.

### `scorpion reconcile-artifacts`

Refresh proof artifact linkage after tests (CI gate).

## Blocked Modes

- `apply` — always blocked in Stage 1–2 with contract error.

## Safety Defaults

- All modes are non-destructive to repository and host.
- Ledger append only in `judge` mode with explicit paths.
- Extraction uses tempfile sandbox only.

## Ledger

- Path default: `.runtime/scorpion/anomaly_ledger.jsonl`
- Version: `scorpion.ledger.v1`
