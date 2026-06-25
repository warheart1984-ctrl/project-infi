# Repo Steward Rule Set

| Field | Value |
|-------|-------|
| **Subsystem** | Repo Steward |
| **Authority** | [ROOT_STRUCTURE_AUDIT.md](../../audit/ROOT_STRUCTURE_AUDIT.md) · [`.gitignore`](../../../.gitignore) |
| **Manifest** | [REPO_HYGIENE_MANIFEST.json](../../audit/REPO_HYGIENE_MANIFEST.json) |
| **Enforcement** | [check-repo-hygiene.py](../../../.github/scripts/check-repo-hygiene.py) |

Repo Steward is **Stage 2 integration hygiene**: it inspects workspace shape and reports drift. It does not delete files or mutate repo content (MA-13 Class III guard).

## Rules

| rule_id | severity | category | trigger | remediation |
|---------|----------|----------|---------|-------------|
| `hygiene.forbidden_root_name` | error | mirror | Root child name in `forbidden_root_names` | Delete locally or never commit; see ROOT_STRUCTURE_AUDIT §3 |
| `hygiene.forbidden_root_glob` | warn | artifact | Root file matches `forbidden_root_globs` | Move off root or delete locally |
| `hygiene.poison_dir` | error | bundle_pollution | Whitespace-only root dir, or `opt/cogos` / `.synthetic-mind-bundle-build` under repo root outside allowed bundle paths | `python scripts/repo/remove-poison-dir.py` (Windows); delete accidental bundle mirror |
| `hygiene.forbidden_tracked` | error | git_index | `git ls-files` path under `forbidden_tracked_prefixes` | `git rm --cached` and fix source |
| `hygiene.local_work_dir` | warn | local_only | Path in `local_work_dirs` exists on disk | Safe to delete when not in active use |
| `hygiene.stale_payload_runtime` | warn | generated_drift | `wolf-cog-os/payload/.../cog_runtime/` differs from fresh Synthetic Mind bundle | Delete payload runtime tree; re-run `stage-nova-cortex-into-payload.sh` |
| `hygiene.stray_root_argv` | warn | sidecar | Root `--*` argv files or stray `bash` / `python3` stubs | Delete per `.gitignore` lines 129–135 |

## Severity semantics

- **error** — workspace pollution that must not persist; `make repo-hygiene-gate` fails when `REPO_HYGIENE_MODE=fail`
- **warn** — local-only or generated drift; reported but does not fail gate unless promoted to error in a future manifest version

## Out of scope

Canonical lane bundle sync is enforced by `check-canonical-lane-sync.py` via `make synthetic-mind-gate`, not Repo Steward errors.
