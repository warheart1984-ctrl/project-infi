# AAIS Project Cleanup Audit

Snapshot date: 2026-04-13

This file separates what is still missing across:

- the current canonical AAIS project
- non-canonical lanes that still exist inside `AAIS-main`
- documented sibling/reference projects outside the current checkout

Evidence rule:

- `AAIS-main` items below are based on live repo code and docs
- outside projects are based on [AAIS_CANONICAL_MAP.md](../runtime/AAIS_CANONICAL_MAP.md) and [REFERENCE_PROJECTS.md](../workspace/REFERENCE_PROJECTS.md)
- if a sibling project is not present in this checkout, it is listed as "not live-verified"

## 1. Current Canonical Project: `AAIS-main`

Status:

- canonical
- functional
- current runtime owner

What is still missing or still needs cleanup:

- the `src/api.py` versus `app/main.py` ownership split is now explicit
  - `src/api.py` owns core Jarvis runtime truth
  - `app/main.py` owns the workflow/onboarding shell and compatibility bridge
- workflow/onboarding pages are now classified as canonical workflow-shell routes
  - they are live product surfaces, not reference-only pages
- `data/chroma/` is now treated as local runtime state instead of canonical source
  - the runtime sqlite store should stay local and ignored by git once untracked
- a real roadmap instead of the thin `roadmap.csv` phase list
- final OTEM expansion decisions beyond the current v5 proposal-only ceiling
- final PatchForge decision between:
  - keeping it permanently review-first
  - or promoting it into a true authoring/apply-capable subsystem
- completion of the remaining manual OpenRouter key-rotation operational step
- removal or replacement of the deprecated `starlette.middleware.wsgi.WSGIMiddleware` bridge in `app/main.py`

## 2. In-Repo Non-Canonical Lanes Inside `AAIS-main`

These are in the worktree, but they still need classification cleanup.

### Workflow / Onboarding lane

Missing:

- explicit canonical decision
- one handbook section explaining whether this is product, staging, or reference
- route and state ownership documentation relative to the main Jarvis shell

### Alternate app/control/api lane

Examples:

- `app/`
- `control/`
- `api/`

Missing:

- one written rule for what owns runtime authority and what is compatibility-only
- either archival labeling or stronger separation from the canonical `src/api.py` spine
- a cleanup pass that removes silent ambiguity for future contributors

### Forge / ForgeEval / EvolveEngine lane

Status now:

- functional bounded lanes
- law envelope and UL contract now implemented

Still missing:

- one consistent canonical statement across docs about whether these are now part of the stable AAIS spine or still "bounded but semi-separate"
- a promotion rule for when a bounded lane becomes fully canonical versus simply integrated

### Root reference/archive material

Examples:

- old `.docx` files
- zip bundles
- older single-file lineage code such as `core.py`, `angels.py`, `god_dashboard.py`

Missing:

- one archive folder or archive policy so the root is not acting as both runtime surface and historical vault
- a keep/delete/archive decision for older bundles that are no longer being mined

## 3. Documented External / Non-Current Projects

These are part of the workspace story, but they were not live-inspected from this checkout.

### `NVIDIA`

Known from docs:

- separate private API / research sandbox

Missing from the AAIS side:

- current verification status
- a documented list of ideas already borrowed into AAIS
- a "do not integrate directly" boundary note tied to specific interfaces

### `mystic`

Known from docs:

- separate small project with its own frontend/repo identity

Missing:

- live verification from the current checkout
- a documented extraction list of what AAIS still wants from it
- consistent mention in all reference-project docs

### `Ui jarvis`

Known from docs:

- visual and voice reference lane

Missing:

- a finished "borrowed already" list versus "still reference-only" list
- an explicit design-kit extraction so the reference repo no longer has to be consulted for basic Jarvis identity work

### `code` / `code\\code`

Known from docs:

- architecture bucket with `evolving_ai` and other references

Missing:

- a selective extraction ledger
- a clear record of what patterns were adopted, rejected, or left unreviewed

### `jarvis`

Known from docs:

- older feature-heavy Jarvis tree

Missing:

- a feature disposition list
  - what AAIS wants to borrow
  - what AAIS explicitly rejects
  - what remains interesting but out of scope

### `Spiral-Companion-main`

Known from docs:

- substantial separate project

Missing:

- current verification
- a written reason it remains non-canonical
- any explicit integration or non-integration plan

### `Nova, The North Star`

Known from docs:

- concept/spec lane for a user-side companion

Missing:

- a live integration boundary doc
- a decision on what is active doctrine versus archived concept material

### `God engine`

Known from docs:

- historical lineage source

Missing:

- a concise lineage summary for what still matters today versus what is fully retired

### `project`

Known from docs:

- scaffold/storage overflow bucket

Missing:

- a retention rule
- an archive/delete policy
- a reason for continued existence if it is not a current product

## 4. Cross-Project Documentation Cleanup Still Needed

These are documentation gaps, not runtime bugs.

- [REFERENCE_PROJECTS.md](../workspace/REFERENCE_PROJECTS.md) needs to stay aligned with [AAIS_CANONICAL_MAP.md](../runtime/AAIS_CANONICAL_MAP.md)
- there should be one source that distinguishes:
  - canonical
  - in-repo non-canonical
  - outside reference-only
  - not live-verified
- each documented sibling project should have either:
  - a current path
  - or a note that it is no longer directly visible from the checked-out repo

## 5. Recommended Cleanup Order

1. Finish the canonical ownership cleanup inside `AAIS-main`.
   - settle `src/api.py` versus `app/main.py`
   - settle workflow/onboarding status
   - define runtime-data handling for `data/chroma`
2. Clean the in-repo reference boundaries.
   - decide which root archives stay
   - move true archive material out of the runtime root where practical
3. Normalize the sibling-project inventory.
   - keep [REFERENCE_PROJECTS.md](../workspace/REFERENCE_PROJECTS.md) and [AAIS_CANONICAL_MAP.md](../runtime/AAIS_CANONICAL_MAP.md) in sync
   - mark which outside projects are not live-verified from this checkout
4. Create a borrow ledger for non-current projects.
   - one line per project
   - borrowed
   - deferred
   - rejected
   - unknown
