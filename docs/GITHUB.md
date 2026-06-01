# GitHub Repository Setup

This document describes how Project Infinity is prepared for GitHub and what stays local-only.

## Remote

- **Repository:** https://github.com/warheart1984-ctrl/Project-Infinity1
- **Default branch:** `main`

## Clean repo principles

| Bucket | Examples | Git treatment |
|---|---|---|
| **Active core** | `src/`, `app/`, `aais/`, `frontend/`, `wolf-cog-os/scripts/`, `deploy/`, `docs/`, `.github/` | Tracked |
| **Local-only** | `.runtime/`, `*.iso`, `wolf-cog-os/output/`, worktrees (`.cogos-*`) | `.gitignore` |
| **Duplicate imports** | `AAIS-main/`, `Project-Infinity-main/`, `Aris--main/` | `.gitignore` |

Inventory authority: [`docs/audit/ROOT_STRUCTURE_AUDIT.md`](audit/ROOT_STRUCTURE_AUDIT.md)

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

A fresh clone excludes multi-GB ISO and forge output directories by design. Build ISOs locally with Wolf-CoG-OS scripts; outputs land under `wolf-cog-os/output/` (ignored).

## Related docs

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md)
- [`../README.md`](../README.md)
- [`audit/ROOT_STRUCTURE_AUDIT.md`](audit/ROOT_STRUCTURE_AUDIT.md)
