# Lab Console v1 Proof Bundle

**Claim label:** `asserted` (single-machine; cross-machine replay inactive)

## Scope

First governed lab project init, session receipt, and experiment artifact layout.

## Verification

```bash
make lab-gate
```

Or:

```bash
python -m pytest tests/test_lab.py tests/test_lab_worktree.py -q
python .github/scripts/check-lab-governance.py --repo-root .
```

## Expected artifacts (after `lab init`)

Under `.runtime/lab/<project_id>/`:

- `LAB_PROJECT_MANIFEST.json`
- `LAB_PROJECT_SPEC.json`
- `LAB_SPINE_PROFILE.json`
- `LAB_CAPABILITY_PROFILE.json`
- `workspace/` (git worktree or clone)
- `experiments/`
- `sessions/`

Ledger: `.runtime/lab/lab_ledger.jsonl`

After `LabSession.close()`:

- `sessions/<session_id>/LAB_SESSION_RECEIPT.json`
- `sessions/<session_id>/pre_snapshot.json`
- `sessions/<session_id>/post_snapshot.json`
- `experiments/exp-NNN-<slug>/` when writes occurred

## Environment

- Repository: project-infi
- Console version: `lab.v1`
- Default spec: `lab/specs/default.yaml`

## Template

See [`templates/PROOF_BUNDLE_TEMPLATE.md`](../../templates/PROOF_BUNDLE_TEMPLATE.md).

## Sign-off

- [ ] Operator verified `LAB_SESSION_RECEIPT.json` for a smoke session
- [ ] `make lab-gate` passed on target machine
