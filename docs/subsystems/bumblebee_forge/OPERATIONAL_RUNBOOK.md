# Bumblebee Forge Operational Runbook (BF-DOC-001 Skeleton)

## Status

| Field | Value |
|---|---|
| Debt ID | `BF-DOC-001` |
| Completeness | **skeleton** (setup + weekly loop; monitoring/incident sections TBD) |
| Claim | `asserted` until SOPs are reviewed and signed off |

Authority: `META_ARCHITECT_LAWBOOK.md`, `STAGE_EXECUTION_PLAYBOOK.md`.

## 1) Setup / Install

### Prerequisites

- Python 3.12 (local validation path; see debt `BF-ENV-001` for matrix alignment)
- Repository root: project-infi
- Dry-run only: do not set `FORGE_CROSS_MACHINE_REPLAY_ACTIVE` unless intentionally replaying

### Initial Bootstrap

```bash
cd <repo-root>
py -3.12 -m unittest tests.test_forgekeeper -v
py -3.12 -m forge.forgekeeper --mode observe --plan-id bf-ops-bootstrap --scope .
```

Expected: exit `0`, `claim_label` in `asserted` or `proven`, `safety_state=dry_run_only`.

### Proof Bundle Paths

| Artifact | Path |
|---|---|
| Stage proof index | `docs/proof/bumblebee-forge/STAGE1_PROOF_BUNDLE.md` |
| Verify export (weekly) | `docs/proof/bumblebee-forge/forgekeeper_verify_report.json` |
| Governance report | `docs/proof/bumblebee-forge/forgekeeper_report.json` |
| Runtime ledger | `.runtime/forgekeeper/decision_ledger.jsonl` |

## 2) Weekly Operator Loop

Derived from `STAGE_EXECUTION_PLAYBOOK.md`. Run from repository root.

### Step A — Architect

- Review `BASELINE_CHECKLIST.md` debt register.
- Confirm no undocumented scope drift in `BUMBLEBEE_FORGE_ROADMAP.md`.

### Step B — Operator (verify export)

Deterministic weekly archive (fixed timestamp for reproducible CI replay):

```bash
py -3.12 -m forge.forgekeeper --mode verify --plan-id bf-weekly --scope . ^
  --fixed-timestamp 2026-05-28T12:00:00Z ^
  --write-report docs/proof/bumblebee-forge/forgekeeper_verify_report.json
```

Record `verify_report_sha256` from CLI output in proof bundle notes.

### Step C — Seam Checker

```bash
py -3.12 -m forge.forgekeeper --mode trace-query --plan-id bf-weekly --scope .
py -3.12 -m forge.forgekeeper --mode reconcile-query --plan-id bf-weekly --scope .
py -3.12 -m forge.forgekeeper --mode drift-window-query --plan-id bf-weekly --scope .
```

If `reconcile-query` reports drift, run one-shot refresh:

```bash
py -3.12 -m forge.forgekeeper --mode reconcile-artifacts --plan-id bf-weekly --scope . \
  --fixed-timestamp 2026-05-28T12:00:00Z
```

Or: `powershell -File scripts/forgekeeper/reconcile-artifacts.ps1`
Or: `bash scripts/forgekeeper/reconcile-artifacts.sh bf-weekly 2026-05-28T12:00:00Z`

Index trend policy: `SNAPSHOT_INDEX_COMPACTION_POLICY.md` (pair-based trend; append-only history).

### Step D — Chaos User

```bash
py -3.12 -m forge.forgekeeper --mode chaos-check --plan-id bf-weekly --scope .
```

Pass gate: `scenarios_passed=3`, `claim_label=proven`.

### Step E — Meta-Inspector

- Update claim labels in `STAGE1_PROOF_BUNDLE.md` if evidence changed.
- Do not promote cross-machine claims while replay is inactive (`BF-XM-001`).

## 3) Standard Procedures (Outlines)

### 3.1 Monitoring and Alerting (outline)

| Signal | Source | Threshold (draft) | Action |
|---|---|---|---|
| Traceability drift | `status` → `traceability_drift.drift_detected` | `true` | Run `reconcile-query`, open ops ticket |
| Verify claim degradation | `forgekeeper_verify_report.json` | `claim_label=rejected` | Seam check + rebuild report/snapshot chain |
| Chaos regression | `chaos-check` | `scenarios_passed < 3` | Block promotion; Debugger + Chaos User review |
| Index trend degradation | `drift-window-query` | `trend=degrading` | Meta-Inspector review; Architect debt triage |
| Cross-machine activation | env `FORGE_CROSS_MACHINE_REPLAY_ACTIVE` | set without approval | Meta-Inspector reject; reset env |

Alert routing owner: `TBD-Forge-Owner` (debt `BF-DOC-002`).

### 3.2 Troubleshooting Decision Tree (outline)

1. **CLI exit code 2** → read `forgekeeper_error`; fix contract inputs (JSON, mode, flags).
2. **`--allow-apply` blocked** → expected; do not bypass. Use dry-run chain only.
3. **`reconcile-query` drift** → run command templates in order: `report` → `snapshot` → `snapshot-index`.
4. **`verify claim_label=rejected`** → inspect `presence_checks` and `traceability_drift.drift_checks`.
5. **`chaos-check` failure** → treat as fail-safe regression; no promotion until tests pass locally and in CI.
6. **Python version mismatch** → see debt `BF-ENV-001`; align runner to 3.12 for validation.

### 3.3 Incident Response and Escalation (outline)

| Severity | Example | Immediate action | Escalation |
|---|---|---|---|
| Low | Single drift check on dev machine | `reconcile-query` + local rebuild chain | Operator |
| Medium | Weekly verify export rejected | Halt promotion; capture `verify --write-report` artifact | Seam Checker → Architect |
| High | Chaos-check fails on main/CI | Halt Forgekeeper-dependent releases | Debugger + Meta-Inspector |
| Critical | Unauthorized apply attempt or env bypass | Kill switch: disable mutating tooling; preserve ledger | Governance reviewer + human authority |

Evidence requirement: append command transcript + hashes to `STAGE1_PROOF_BUNDLE.md`.

### 3.4 Release / Deployment Procedure (outline)

1. CI gate passes: `.github/workflows/forgekeeper-governance-gate.yml`.
2. Operator archives deterministic verify export (`--fixed-timestamp`).
3. Meta-Inspector confirms claim taxonomy in proof bundle.
4. Cross-machine replay remains **inactive** unless `BF-XM-001` is explicitly closed.
5. Sign-off recorded in proof bundle §7 before readiness promotion.

Remaining depth (full SOP prose): debt `BF-DOC-001` (monitoring/incident/release sections).

## 4) CI Governance Gate (read-only)

Local/CI entrypoint:

```bash
python3 .github/scripts/check-forgekeeper-governance.py --repo-root .
```

Workflow: `.github/workflows/forgekeeper-governance-gate.yml`

Gate checks (non-destructive):

- `unittest tests.test_forgekeeper`
- `chaos-check` must return `claim_label=proven`
- `verify --write-report` with fixed timestamp (warn-only on verify `rejected` unless `--strict-verify-claim`)
- `bundle-export` manifest generation
- cross-machine replay must remain `inactive`

## 5) Bundle Export (weekly archive)

```bash
py -3.12 -m forge.forgekeeper --mode bundle-export --plan-id bf-weekly --scope . \
  --fixed-timestamp 2026-05-28T12:00:00Z \
  --write-bundle-export docs/proof/bumblebee-forge/forgekeeper_bundle_manifest.json
```

## 6) Failsafe

- `--allow-apply` is blocked in all modes.
- Kill switch: stop using mutating tooling outside Forgekeeper contract.
- Recovery: `report` → `snapshot` → `snapshot-index` per `reconcile-query` hints.

## 7) Cross-Machine (Inactive)

See `CROSS_MACHINE_REPLAY.md`. Do not activate until second machine is ready.
