# Forgekeeper CLI Contract

## Status

Stage: 1/2 runtime scaffold
Claim: `asserted` for full workflow acceptance, `proven` for local skeleton execution evidence.

Runtime entrypoint: `py -3.12 -m forge.forgekeeper`
Implementation file: `forge/forgekeeper.py`
Focused tests: `tests/test_forgekeeper.py`

## Contract Intent

Define a safe command surface for reconstruction workflows with dry-run defaults
and explicit mode gating.

## Command Set

### `forgekeeper observe`

Read-only observation summary of scope/goal/focus without generating a plan.

Required inputs:

- `--plan-id <id>`

Optional inputs:

- `--scope <path-or-logical-target>`
- `--goal <text>`
- `--focus-file <path>` (repeatable)
- `--constraints-json <json-object>`

Default mode: read-only.

### `forgekeeper plan`

Generate a bounded reconstruction plan without mutating repository state.

Required inputs:

- `--scope <path-or-logical-target>`
- `--goal <text>`

Optional inputs:

- `--focus-file <path>` (repeatable)
- `--proof-bundle-ref <path>`
- `--constraints-json <json-object>`
- `--write-plan <path>`

Default mode: dry-run only.

### `forgekeeper judge`

Create a read-only gate decision record for a proposed plan.

Required inputs:

- `--plan-id <id>`
- `--decision <approve|reject>`
- `--reason <text>`

Optional inputs:

- `--reviewer <id>`
- `--allow-approve`
- `--evidence-ref <path-or-id>` (repeatable)
- `--ledger-path <path>`

Behavior:

- `reject` always allowed.
- `approve` requires explicit reviewer identity and reason.
- `approve` is blocked unless `--allow-approve` is present.
- command emits `decision_record` scaffold for Stage 3 ledger integration.
- command appends one JSON object per line to an append-only ledger.

### `forgekeeper status`

Print current plan, gate, and claim states.

Optional inputs:

- `--plan-id <id>`
- `--output <json|text>`
- `--ledger-path <path>`
- `--report-path <path>`

Status payload now includes:

- `report_path`
- `report_sha256` (when report exists)
- `report_claim_label` (when report is parseable)
- `snapshot_path`
- `snapshot_sha256` (when snapshot exists)
- `snapshot_claim_label` and `snapshot_id`
- `snapshot_index_path`
- `snapshot_index` summary and `snapshot_index_sha256` (when index exists)
- `snapshot_index_recent` (up to last 3 records)
- `snapshot_index_window` (latest claim-label window summary)
- `traceability` existence flags across ledger/report/snapshot/index
- `traceability_drift` (`drift_detected`, failed check names, claim label)

### `forgekeeper report`

Generate one non-destructive proof/export report JSON that summarizes plan,
ledger, and evidence hash manifest.

Required inputs:

- `--plan-id <id>`

Optional inputs:

- `--proof-dir <path>`
- `--plan-artifact <path>` (auto-discovers newest `*plan*.json` when omitted)
- `--ledger-path <path>`
- `--report-path <path>`
- `--ledger-tail <int>`
- `--fixed-timestamp <utc-timestamp>`
- `--evidence-ref <path-or-id>` (repeatable)

### `forgekeeper snapshot`

Emit immutable snapshot metadata that links current report and ledger state.

Required inputs:

- `--plan-id <id>`

Optional inputs:

- `--report-path <path>`
- `--ledger-path <path>`
- `--snapshot-path <path>`
- `--fixed-timestamp <utc-timestamp>`
- `--evidence-ref <path-or-id>` (repeatable)

### `forgekeeper snapshot-index`

Append one immutable index record to snapshot-history JSONL.

Required inputs:

- `--plan-id <id>`

Optional inputs:

- `--snapshot-path <path>`
- `--report-path <path>`
- `--ledger-path <path>`
- `--snapshot-index-path <path>`
- `--supersedes-snapshot-id <id>`
- `--fixed-timestamp <utc-timestamp>`
- `--evidence-ref <path-or-id>` (repeatable)

### `forgekeeper snapshot-query`

Query snapshot-index records without mutating artifacts.

Required inputs:

- `--plan-id <id>`

Optional inputs:

- `--snapshot-index-path <path>`
- `--query-snapshot-id <id>`
- `--query-claim-label <asserted|proven|rejected>`
- `--query-since-utc <utc-timestamp>`
- `--query-limit <int>`

### `forgekeeper trace-query`

Query governance traceability across ledger/report/snapshot/index artifacts.

Required inputs:

- `--plan-id <id>`

Optional inputs:

- `--ledger-path <path>`
- `--report-path <path>`
- `--snapshot-path <path>`
- `--snapshot-index-path <path>`
- `--query-ledger-claim-status <asserted|proven|rejected>`
- `--query-reviewer <id>`
- `--query-since-utc <utc-timestamp>`
- `--query-limit <int>`

### `forgekeeper reconcile-query`

Emit read-only reconciliation hints from current traceability drift.

Required inputs:

- `--plan-id <id>`

Optional inputs:

- `--ledger-path <path>`
- `--report-path <path>`
- `--snapshot-path <path>`
- `--snapshot-index-path <path>`
- `--query-ledger-claim-status <asserted|proven|rejected>`
- `--query-reviewer <id>`
- `--query-since-utc <utc-timestamp>`
- `--query-limit <int>`

### `forgekeeper drift-window-query`

Analyze snapshot-index claim transitions over a bounded time window.

Required inputs:

- `--plan-id <id>`

Optional inputs:

- `--snapshot-index-path <path>`
- `--query-since-utc <utc-timestamp>`
- `--query-limit <int>`

## Mode Gating (Current Runtime)

- `observe` mode:
  - allowed behavior: read-only summary
  - denied behavior: apply/mutate
- `plan` mode:
  - allowed behavior: deterministic dry-run plan generation
  - denied behavior: apply/mutate
- `judge` mode:
  - allowed behavior: read-only decision emission
  - denied behavior: execution authorization without explicit approve gate
- `status` mode:
  - allowed behavior: read-only state echo
  - denied behavior: apply/mutate
- `report` mode:
  - allowed behavior: read-only proof aggregation and export
  - denied behavior: apply/mutate
- `snapshot` mode:
  - allowed behavior: read-only immutable metadata emission
  - denied behavior: apply/mutate
- `snapshot-index` mode:
  - allowed behavior: append-only history index metadata
  - denied behavior: apply/mutate
- `snapshot-query` mode:
  - allowed behavior: read-only index filtering and retrieval
  - denied behavior: apply/mutate
- `trace-query` mode:
  - allowed behavior: read-only cross-artifact traceability correlation
  - denied behavior: apply/mutate
- `reconcile-query` mode:
  - allowed behavior: read-only reconciliation hint generation
  - denied behavior: apply/mutate
- `drift-window-query` mode:
  - allowed behavior: read-only trend analysis over snapshot-index history
  - denied behavior: apply/mutate
- `verify` mode:
  - allowed behavior: one-click read-only verification across proof artifacts
  - denied behavior: apply/mutate
- `chaos-check` mode:
  - allowed behavior: in-memory adversarial drills with expected claim outcomes
  - denied behavior: apply/mutate and repository artifact mutation
- `bundle-export` mode:
  - allowed behavior: consolidated hash manifest + verify/chaos summaries
  - denied behavior: apply/mutate

Hard safety gate:

- `--allow-apply` is currently rejected in all modes with non-zero exit code.

## Error Contract

Error codes:

- `invalid_request`
- `contract_violation`
- `law_violation`
- `gate_denied`
- `expired_gate`
- `apply_blocked`

Error payload minimum:

- code
- message
- containment_state
- claim_label (`asserted` or `rejected`)

## Evidence Requirements Per Command

- record exact command line and exit status.
- store machine-readable output where applicable.
- append claim label and proof link in proof bundle.

## Stage 2 Deterministic Plan Scaffold

Plan output includes:

- deterministic seed derived from request fields
- rollback token placeholder (`rbk-<seed-prefix>`)
- serializable change graph (`change_nodes`, `change_edges`)
- evaluable attestation hooks:
  - `law_precheck`
  - `scope_boundary_precheck`
  - `evidence_reference_precheck`
- attestation overall claim label (`proven`/`asserted`/`rejected`)

## Decision Ledger

Default ledger path:

- `.runtime/forgekeeper/decision_ledger.jsonl`

Ledger record fields include:

- timestamp (`recorded_at_utc`)
- mode
- decision
- claim_status
- evidence_refs
- reviewer and reason

## Proof Export Report

Default report path:

- `docs/proof/bumblebee-forge/forgekeeper_report.json`

Report payload includes:

- plan artifact summary and claim label
- latest ledger summary and tail entries
- evidence reference integrity checks
- hash manifest for plan, ledger, and evidence refs
- overall claim label (`proven`, `asserted`, `rejected`)

Determinism controls:

- fixed timestamp override (`--fixed-timestamp`) for reproducible exports
- stable JSON serialization (`sort_keys=true`)
- deterministic hash manifest ordering by `artifact` then `path`

## Snapshot Metadata

Default snapshot path:

- `docs/proof/bumblebee-forge/forgekeeper_snapshot.json`

Snapshot payload includes:

- `snapshot_id`
- `created_at_utc`
- claim taxonomy label
- report hash and claim label
- ledger hash and entry count
- evidence refs and integrity labels
- immutable metadata flag

Status linkage includes:

- `snapshot_path`
- `snapshot_sha256`
- `snapshot_claim_label`
- `snapshot_id`
- `snapshot_index_recent`

## Snapshot Index Manifest

Default index path:

- `docs/proof/bumblebee-forge/forgekeeper_snapshot_index.jsonl`

Index record includes:

- `index_id`
- `created_at_utc`
- `claim_label`
- `claim_transition` (`previous->current`)
- `supersedes_snapshot_id`
- `snapshot_id`
- snapshot/report/ledger hashes
- evidence refs with integrity labels

Query output includes:

- applied filters
- matched and total entry counts
- filtered result set
- latest transition/index summary

Trace-query output includes:

- filtered ledger matches (`claim_status`, reviewer, time window)
- report/snapshot/index claim summaries and hashes
- explicit traceability checks for snapshot/index hash linkage to current artifacts
- aggregate claim label (`proven`/`asserted`/`rejected`)

Reconcile-query output includes:

- drift check subset (`claim_label=rejected`)
- deterministic remediation hints and command templates
- recommendation claim label (`proven` when no drift, otherwise `asserted`)

Drift-window-query output includes:

- bounded claim-label window extracted from snapshot-index
- trend classification (`improving`, `stable`, `degrading`, `recovered`, `insufficient_data`)
- trend basis (`pair` = latest two entries only; default)
- trend claim label (`proven`/`asserted`/`rejected`)

Policy: `SNAPSHOT_INDEX_COMPACTION_POLICY.md`

## Verify Command

Read-only consolidated verification across presence checks, trace,
reconciliation, and drift summaries.

```bash
py -3.12 -m forge.forgekeeper --mode verify --plan-id <id> --scope .
py -3.12 -m forge.forgekeeper --mode verify --plan-id <id> --scope . \
  --fixed-timestamp 2026-05-28T12:00:00Z \
  --write-report docs/proof/bumblebee-forge/forgekeeper_verify_report.json
```

`--write-report` accepts an optional path; default export path is
`docs/proof/bumblebee-forge/forgekeeper_verify_report.json`.

Determinism: combine `--fixed-timestamp` with stable JSON serialization for
byte-stable exports when artifact inputs are unchanged.

Output includes:

- `presence_checks` for proof dir, ledger, report, snapshot, index, latest plan
- `trace_claim_label`, `reconcile_claim_label`, `drift_claim_label`
- `verification_steps` replay command list
- overall `claim_label`

## Chaos-Check Command

Runs temporary adversarial scenarios only (no repository mutation):

- missing ledger
- corrupt report JSON
- snapshot hash drift

```bash
py -3.12 -m forge.forgekeeper --mode chaos-check --plan-id <id> --scope .
```

Pass criteria: all scenarios report `passed=true` and overall `claim_label=proven`.

## Reconcile Artifacts Command

Refreshes `report` → `snapshot` → `snapshot-index` in order so linkage hashes
match the current append-only ledger (run after tests or judge activity).

```bash
py -3.12 -m forge.forgekeeper --mode reconcile-artifacts --plan-id <id> --scope . \
  --fixed-timestamp 2026-05-28T12:00:00Z
```

## Bundle Export Command

```bash
py -3.12 -m forge.forgekeeper --mode bundle-export --plan-id <id> --scope . \
  --fixed-timestamp 2026-05-28T12:00:00Z \
  --verify-report-path docs/proof/bumblebee-forge/forgekeeper_verify_report.json \
  --write-bundle-export docs/proof/bumblebee-forge/forgekeeper_bundle_manifest.json
```

Output includes sorted `hash_manifest`, `verification_summary`, `chaos_summary`,
and optional `bundle_export_sha256` when written.

## CI Governance Gate

Read-only gate script:

```bash
python3 .github/scripts/check-forgekeeper-governance.py --repo-root .
```

Workflow: `.github/workflows/forgekeeper-governance-gate.yml`

## Cross-Machine Replay (Built, Inactive)

Scaffold only. `verify` output includes `cross_machine_replay` with
`operational_status=inactive` unless `FORGE_CROSS_MACHINE_REPLAY_ACTIVE=1`.

Activation docs: `CROSS_MACHINE_REPLAY.md`
Drivers: `scripts/forgekeeper/cross-machine-replay.ps1` / `.sh`

## Example Safe Flow

1. `py -3.12 -m forge.forgekeeper --mode observe --plan-id bf-plan-001 --scope src`
2. `py -3.12 -m forge.forgekeeper --mode plan --plan-id bf-plan-001 --scope src --goal "bounded reconstruction map"`
3. `py -3.12 -m forge.forgekeeper --mode judge --plan-id bf-plan-001 --decision reject --reason "attestation pending"`

Execution/apply step remains intentionally unavailable and `asserted` only.
