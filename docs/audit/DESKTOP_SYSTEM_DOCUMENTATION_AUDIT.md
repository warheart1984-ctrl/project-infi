# Desktop System Documentation Audit

Snapshot date: 2026-04-15

This file audits repo documentation against the current verified desktop AAIS
system.

The goal is to separate:

- missing documentation for live desktop/runtime surfaces
- stale documentation that no longer matches the verified app
- non-canonical documentation or documentation-like artifacts that can still be
  mistaken for active project truth

## Verification Basis

This audit was checked against the currently verified desktop-facing surfaces:

- `.venv\\Scripts\\python.exe -m pytest -q tests\\test_aais_launcher.py tests\\test_app_packaged_frontend.py tests\\test_app_main_health.py`
  - result: `8 passed`
- `frontend\\npm.cmd run test:ci`
  - result: `28 passed`
- `frontend\\npm.cmd run build`
  - result: passed
- `.venv\\Scripts\\python.exe -m aais doctor --data-dir .\\.runtime\\aais-data`
  - result: packaged frontend ready, frontend build ready, `/app` desktop shell
    path configured

## 1. Missing Documentation Relative To The Verified Desktop System

### A. No canonical desktop launcher/package runbook in `docs/`

Current state:

- the verified desktop launcher exists in `aais/launcher.py`
- `aais/README.md` now provides a local folder entry doc for the launcher package
- packaging metadata exists in `pyproject.toml`
- `python -m aais start`, `prepare`, and `doctor` are documented in the root
  `README.md`

Missing:

- one canonical desktop/launcher runbook inside the `docs/` tree

Why this matters:

- the current desktop path is real and verified, but its canonical doc path is
  still split across the root README, frontend README, and `aais/README.md`
- there is still no docs-tree runbook that treats launcher/package behavior as a
  first-class canonical surface

### B. Core live folders still lack local entry docs

The verified desktop system still lacks folder-local entry docs for several
live directories. See [FOLDER_DOCUMENTATION_AUDIT.md](./FOLDER_DOCUMENTATION_AUDIT.md)
for the full inventory.

Highest-impact remaining gaps:

- `api/`
- `tests/`
- `data/`
- `evals/`
- `docs/`

Why this matters:

- the central doc spine explains the system at a high level
- local folder entry docs are still missing in the places a contributor opens
  first when working on the launcher, shell, runtime, or verification layers

## 2. Stale Documentation Against The Verified Desktop App

### `frontend/README.md`

Stale/incomplete state:

- it still frames the frontend mainly as a general multi-modal UI with the old
  feature list of dashboard, text/image/audio tools, history, and settings
- it does not clearly describe the current Small Nova home surface, Repo
  Manager route, or the fact that the packaged desktop shell is a first-class
  path rather than an afterthought

Why it is only partially stale:

- the build and test commands are still correct
- the packaged `/app` staging notes are still correct
- the route/feature summary is now behind the verified app shape

## 3. Non-Canonical Or Misleading Documentation Still Present

### A. `docs/audit/COMPONENT_AUDIT.md`

Problem:

- this file reads like an active "complete system" authority document
- it claims broad implementation coverage such as RBAC, Kafka, Elasticsearch,
  Stable Diffusion 2, and dark mode support

Why this is misleading:

- it does not match the current verified desktop-system reading path
- it is a broad legacy-style inventory, not the current trustworthy source for
  what the desktop AAIS system actually is

Recommended treatment:

- keep only as lineage/reference
- archive it or explicitly mark it as legacy broad inventory
- do not present it in indexes as equal to the live desktop-system audits

### B. Root zip/txt lineage artifacts

Examples still at repo root:

- `aais_ul_pack.zip`
- `jarvis turn key.zip`
- `jarvis_angels_and_wards.zip`
- `law and del handbook.zip`
- `tinynovamemorybank.zip`
- `demo_output.txt`

Problem:

- these are documentation-like lineage/support artifacts sitting beside live
  runtime entrypoints
- they can still be mistaken for current project documentation or active
  desktop-system authority

Recommended treatment:

- move them under `docs/archive/` or another explicit archive/support location
- or add a top-level archive policy that names them as non-canonical artifacts

## 4. Active Canonical Docs That Still Track The Verified Desktop System Well

These remain aligned with the verified desktop system:

- `README.md`
  - current cross-platform launcher commands are correct
- `aais/README.md`
  - now gives the launcher package a folder-local truth anchor
- `app/README.md`
  - now gives the workflow shell a folder-local truth anchor
- `src/README.md`
  - now gives the Jarvis runtime spine a folder-local truth anchor
- `docs/spine/AAIS_HUMAN_GUIDE.md`
  - correctly names Small Nova as the installed companion surface
- `docs/spine/AAIS_AI_OPERATING_CONTRACT.md`
  - correctly names Small Nova as the current default surface
- `docs/spine/AAIS_MASTER_SPEC.md`
  - correctly models Small Nova as installed and the workflow shell as live
- `docs/runtime/AAIS_SYSTEM_HANDBOOK.md`
  - correctly describes the workflow shell, legacy bridge, and packaged `/app`
    shell path
- `docs/subsystems/nova/*.md`
  - the Nova pack is aligned on Small Nova as installed and Tiny Nova as the
    lighter available stage

## 5. Recommended Cleanup Order

1. Add a canonical desktop launcher/package runbook in `docs/`.
2. Refresh `frontend/README.md` so its route and feature summary matches the
   verified desktop app.
3. Fill the remaining local folder entry-doc gaps listed in
   [FOLDER_DOCUMENTATION_AUDIT.md](./FOLDER_DOCUMENTATION_AUDIT.md).
4. Move or explicitly label root zip/txt lineage artifacts so they stop reading
   like current project documents.
5. Downgrade `COMPONENT_AUDIT.md` from active-authority status.
