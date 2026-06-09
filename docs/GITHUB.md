# GitHub Repository Setup

This document describes how Project Infinity is prepared for GitHub and what stays local-only.

## Remote

- **Repository:** https://github.com/warheart1984-ctrl/Project-Infinity1
- **Default branch:** `main`
- **License:** [Apache 2.0](../LICENSE)
- **Release history:** [CHANGELOG.md](../CHANGELOG.md) · [Release tracks](releases/README.md)

## Clean repo principles

| Bucket | Examples | Git treatment |
|---|---|---|
| **Active core** | `src/`, `app/`, `aais/`, `frontend/`, `cog-os/`, `deploy/`, `docs/`, `.github/` | Tracked |
| **Local-only** | `.runtime/`, `*.iso`, `artifacts/cog-os/`, worktrees (`.cogos-*`) | `.gitignore` |
| **Duplicate imports** | `AAIS-main/`, `Project-Infinity-main/`, `Aris--main/` | `.gitignore` |

Inventory authority: [`docs/audit/ROOT_STRUCTURE_AUDIT.md`](audit/ROOT_STRUCTURE_AUDIT.md)

---

## Public Release Manifest

Single source of truth for what belongs in a public clone.

### Include (public core)

| Category | Paths |
|---|---|
| AAIS runtime | `src/`, `app/`, `aais/`, `frontend/`, `app/static/` |
| Packaging | `pyproject.toml`, `requirements*.txt`, `Dockerfile`, `deploy/` |
| Subsystems | `forge/`, `platform/`, `scorpion/`, `mechanic/`, `cog-os/` |
| Governance + docs | `docs/` (active tree), `document/`, root law MD files, `.github/` |
| Tests/tools | `tests/`, `tools/` |
| Legal/setup | `LICENSE`, `SECURITY.md`, `.env.example`, `CHANGELOG.md` |

### Exclude or scrub

| Item | Action |
|---|---|
| `cog-os/payload/opt/cogos/memory/backups/*` | Gitignored — may contain signing keys; never commit |
| `artifacts/cog-os/`, `*.iso` | Gitignored — build outputs |
| `.runtime/`, `.env`, API keys | Gitignored — runtime state and secrets |
| `training/data/private_messages*.jsonl` | Gitignored — private training data |
| Duplicate imports (`*-main/`) | Gitignored |
| `ci-artifacts/`, `debug-*.log`, `release/` | Gitignored — local CI scratch |

### Keep but label clearly

| Item | Treatment |
|---|---|
| [`docs/_archive/`](_archive/) | Historical lineage — not active operator truth |
| [`archive/`](../archive/) | Same |
| [`external/`](../external/) | Vendored third-party code — check each package license |
| Dev compose secrets in `mechanic/hosted/deploy/` | Local pilot only — rotate before production |

---

## Pre-tag release checklist

Run before tagging an AAIS semver release (e.g. `v0.2.0`):

1. **Hygiene gate:** `python .github/scripts/check-repo-hygiene.py` (or `make repo-hygiene-gate`)
2. **Secret scan:** confirm no real keys in tree — especially Wolf-CoG-OS backup bundles
3. **Staged set:** `git status` — no ISOs, `.runtime/`, or artifacts
4. **Docs:** CHANGELOG dated section, README operator path, First-Time Operator Guide current
5. **Tests:**
   ```bash
   python -m pytest tests/test_cisiv.py tests/test_chat_turn_governance.py -q
   python -m tools.ul.smoke
   python -m aais doctor --data-dir ./.runtime/aais-data
   ```
6. **Clone smoke:** fresh `pip install -e .` + `aais start --preset mock --no-browser`
7. **Tag + release:** see [releases/README.md](releases/README.md) for AAIS vs CoGOS tracks

---

## First push checklist (maintainer)

```bash
git status                    # should show no ISOs or .runtime/
git add -A
git status                    # verify staged set
git commit -m "..."
git push origin main
```

## CI workflows

Workflows live in `.github/workflows/`. Path-filtered gates run on PRs when relevant files change; core `cogos-ci-public.yml` runs on all PRs to `main`.

## Clone size

A fresh clone excludes multi-GB ISO and forge output directories by design. Build rootfs and ISOs locally with `cog-os/forge/scripts/`; outputs land under `artifacts/cog-os/` (ignored).

## Related docs

- [First-Time Operator Guide](operations/FIRST_TIME_OPERATOR_GUIDE.md)
- [../CONTRIBUTING.md](../CONTRIBUTING.md)
- [../README.md](../README.md)
- [../SECURITY.md](../SECURITY.md)
- [audit/ROOT_STRUCTURE_AUDIT.md](audit/ROOT_STRUCTURE_AUDIT.md)
