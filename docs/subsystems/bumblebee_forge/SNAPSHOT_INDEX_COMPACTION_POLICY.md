# Snapshot Index Compaction Policy (BF-OPS-011)

## Status

| Field | Value |
|---|---|
| Debt ID | `BF-OPS-011` |
| Policy | **active** (pair-based trend + reconcile baseline) |
| Claim | `asserted` until archival automation is implemented |

## Problem

`forgekeeper_snapshot_index.jsonl` is **append-only** by design. Each
`reconcile-artifacts` run appends a new line. Historical `proven->asserted`
transitions remain in the file forever.

Without policy, `drift-window-query` compared the **oldest** and **newest**
labels in the window and could report `degrading` even when the latest
artifact linkage is healthy.

## Principles

1. **Never delete** index history silently (repo law / proof governance).
2. **Artifact sync** is authoritative for verify (`artifact_sync_claim_label`).
3. **Claim trend** is advisory and uses only the **latest pair** of index entries.
4. **Reconcile-artifacts** is the supported way to establish a fresh baseline row.

## Operator Rules

### After tests, CI, or judge activity

Run reconcile before weekly verify:

```bash
bash scripts/forgekeeper/reconcile-artifacts.sh bf-weekly 2026-05-28T12:00:00Z
```

### Interpreting drift-window trend

| Trend | Meaning |
|---|---|
| `stable` | Latest two index claim labels match rank |
| `improving` | Latest label rank higher than previous |
| `recovered` | Older window had degradation; latest pair is healthy |
| `degrading` | Latest pair shows strict rank drop (action: reconcile) |
| `insufficient_data` | Fewer than two entries in window |

### When trend is `degrading` but verify is `proven`

- Trust **artifact sync** (`reconcile_drift_count=0`).
- Treat trend as historical noise until next reconcile append stabilizes pairs.
- Do not promote cross-machine claims based on trend alone.

## Archival (future, not automated)

When index line count exceeds operator threshold (recommended: 50):

1. Copy full file to `docs/proof/bumblebee-forge/archive/forgekeeper_snapshot_index.<UTC>.jsonl`
2. Keep original append-only file intact OR rotate with human sign-off
3. Record archive hash in `STAGE1_PROOF_BUNDLE.md`

Automation for archival remains **out of scope** until `BF-OPS-011` is closed.

## CI Behavior

The governance gate runs `reconcile-artifacts` after tests, then strict
artifact-sync verify. Claim trend is not a gate failure condition.

## Related Commands

- `reconcile-artifacts` — append baseline row with current hashes
- `drift-window-query` — pair-based trend (default window tail)
- `snapshot-query` — filter index history for audits
