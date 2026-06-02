# Repo Steward v1 Proof Bundle

| Field | Value |
|-------|-------|
| **Claim** | Repo Steward workspace hygiene gate detects forbidden root pollution and mirror drift |
| **Claim posture** | `proven` (local + CI verification) |
| **Authority** | [REPO_PROOF_LAW.md](../../REPO_PROOF_LAW.md) · [ROOT_STRUCTURE_AUDIT.md](../../audit/ROOT_STRUCTURE_AUDIT.md) |

## Scope

- Machine-readable manifest: [REPO_HYGIENE_MANIFEST.json](../../audit/REPO_HYGIENE_MANIFEST.json)
- Gate script: [.github/scripts/check-repo-hygiene.py](../../../.github/scripts/check-repo-hygiene.py)
- CI workflow: [.github/workflows/repo-hygiene-gate.yml](../../../.github/workflows/repo-hygiene-gate.yml)
- Make target: `make repo-hygiene-gate`

## Verification

```bash
python3 -m unittest tests.test_check_repo_hygiene_script -q
make repo-hygiene-gate REPO_HYGIENE_MODE=fail
```

## Rollout

| Milestone | Mode | Status |
|-----------|------|--------|
| Sprint 0 landing | `warn` | complete |
| Sprint 1 close | `fail` | `proven` (Makefile default `REPO_HYGIENE_MODE=fail`) |

## MA-13

Repo Steward inspects workspace shape only; it does not delete files or mutate repo content (Stage 2 integration hygiene, not Stage 3 actuation).

## Operator note (2026-06-02 purge)

Manual purge removed duplicate import trees, root ISOs, sidecars, and stale payload runtime. On Windows, whitespace-only root directories require extended-path removal — do **not** use plain `shutil.rmtree('.\\ ')` (path normalization can target the repo root). Use:

```powershell
python scripts/repo/remove-poison-dir.py
```

Or the one-liner: `python -c "import os; root=os.getcwd(); p='\\\\?\\'+root+os.sep+' '; d='\\\\?\\'+root+os.sep+'_poison_dir_delete_me'; os.rename(p,d); os.rmdir(d)"`

Close IDE/git handles first if WinError 32 persists.
