# Coding Organs Subsystem Contract

Status: **active contract**

Unified subsystem for inspect → scope → propose → preview → verify → apply → ledger.

## Stages

1. **Scope** — `change_scope` analyzes workspace impact
2. **Propose** — `patchforge` generates proposal-only plans
3. **Preview** — `patch_execution_preview` surfaces pre-apply review
4. **Verify** — `patch_verification` + `test_oracle` gate apply
5. **Apply** — `patch_apply_engine` with operator approval
6. **Ledger** — `run_ledger` records governed execution

## Invariants

- PatchForge remains proposal-only until verification passes
- Silent apply is forbidden
- All apply paths require operator review when `apply_requires_review=True`
