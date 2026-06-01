# Project Scorpion Subsystem

Governed OS-level anomaly extractor for behavioral invariant drift.

## Intent

Scorpion attaches to OS behavioral traces (fixture-first, then Wolf CoG Linux runtime)
and hunts structural bugs by enforcing truth patterns—not signatures or heuristics.

## Active Docs In This Folder

- `SCORPION_BLUEPRINT.md` — architecture, five components, non-goals
- `SCORPION_CLI_CONTRACT.md` — command semantics and mode gating
- `SCORPION_ROADMAP.md` — staged delivery map (Stage 0–4)
- `STAGE_EXECUTION_PLAYBOOK.md` — eight-role stage ladder
- `BASELINE_CHECKLIST.md` — baseline governance and documentation debt register
- `OPERATIONAL_RUNBOOK.md` — operator loop skeleton (Stage 2+)
- `WOLF_COG_SEAM.md` — Stage 3 Wolf CoG integration
- `SNAPSHOT_INDEX_COMPACTION_POLICY.md` — index retention policy
- `CROSS_MACHINE_REPLAY.md` — cross-machine replay scaffold (built, inactive)
- `KERNEL_SENTINEL_DESIGN.md` — Stage 4 native Sentinel design

## Proof Artifacts

- `../../proof/scorpion/STAGE0_PROOF_BUNDLE.md`
- `../../proof/scorpion/STAGE1_PROOF_BUNDLE.md` … `STAGE2_PROOF_BUNDLE.md`
- `../../proof/scorpion/STAGE3_PROOF_BUNDLE.md`
- `../../proof/scorpion/kernel_sentinel/STAGE4_PROOF_BUNDLE.md`
- `../../proof/scorpion/scorpion_report.json`
- `../../proof/scorpion/scorpion_snapshot.json`
- `../../proof/scorpion/scorpion_snapshot_index.jsonl`
- `../../proof/scorpion/health_drift_index.jsonl`
- `../../../.runtime/scorpion/anomaly_ledger.jsonl`

## Runtime Scaffold

- `scorpion/scorpion.py` — non-destructive CLI entrypoint
- `tests/test_scorpion.py` — determinism, gating, ledger, chaos drills

## Rule

This subsystem is subordinate to:

1. `META_ARCHITECT_LAWBOOK.md`
2. `REPO_PROOF_LAW.md`
3. active project contracts and runtime constraints

No proof, no claim.
