# Scorpion Snapshot Index Compaction Policy

Append-only `scorpion_snapshot_index.jsonl` records claim transitions and hash linkage.

## Interpretation

- Pair latest two entries for trend (`improving` / `stable` / `degrading`) via `drift-window-query` on `health_drift_index.jsonl`.
- Supersession tracked via `supersedes_snapshot_id` on each index row.

## Archival (debt)

Automated compaction is not implemented. Operators may archive cold index segments to `docs/proof/scorpion/archive/` with manifest hashes when retention SOP is approved.
