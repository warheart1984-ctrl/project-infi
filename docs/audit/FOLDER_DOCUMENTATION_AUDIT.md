# Folder Documentation Audit

Snapshot date: 2026-04-21

This file records which project folders already have adequate documentation,
which are covered only by higher-level docs, and which still need a local
entry document.

Method:

- scanned project-owned folders from the repo root through the active
  subsystem tree
- treated a local folder document as a file that helps a reader opening that
  folder understand what it is, what owns it, and where the truth lives
- treated generated, vendor, build, and runtime-artifact folders as
  non-canonical for missing-document counting
- used the current canonical doc spine plus local folder contents as evidence

Summary:

- high-priority missing local folder docs: 0
- centrally covered but still worth adding local entry docs: 0
- ambiguous folders needing cleanup/classification more than a handbook: 2

## 1. Missing Local Folder Documents Now

No current high-priority local folder documentation gaps remain in the
project-owned top-level tree.

## 2. Active Folders Covered Centrally But Still Missing Local Entry Docs

No current centrally covered-but-missing top-level folder entry docs remain in
the active project tree.

## 3. Adequately Documented, No Immediate Local Doc Gap

- `aais/`
- `app/`
- `api/`
- `data/`
- `docs/`
- `docs/subsystems/`
- `evals/`
- `frontend/`
- `mobile/`
- `src/`
- `tests/`
- `training/`
- `evolve_engine/`
- `forge/`
- `forge_eval/`
- `data/chroma/`
- `docs/archive/`
- `docs/audit/`
- `docs/contracts/`
- `docs/runtime/`
- `docs/spine/`
- `docs/subsystems/nova/`
- `docs/workspace/`

## 4. Not Counted As Missing-Document Folders

These are generated, vendor, build, or runtime-artifact areas and should not
drive canonical documentation expectations.

- `.runtime/`, `.pytest_cache/`, `__pycache__/`
- `.venv*`, `env/`
- `build/`, `dist/`, `app/static/`, `training/out/`
- `.local/`, `.vercel/`, `.vs/`

## 5. Ambiguous Or Cleanup-Sensitive Folders

- `control/`
  - current state: appears to be runtime/broker residue rather than an authored
    subsystem
  - action needed: keep/archive/remove decision before writing a local handbook
- `api/src/`
  - current state: should be documented through `api/README.md`
  - action needed: keep it subordinate to the `api/` compatibility note instead
    of treating it as a separate authority surface

## 6. Maintenance Rule

Folder entry docs now exist for the active top-level project-owned folders.

Keep them aligned whenever:

1. folder ownership changes
2. a new authority surface appears
3. project-wide law changes
4. the external suggestion admission rule changes
