# Jarvis Sibling Truth Audit

Snapshot date: 2026-04-16

Scope:

- `C:\Users\randj\Desktop\project infi\jarvis`
- `C:\Users\randj\Desktop\project infi\jarvis\jarvis`

Goal:

- identify the real supported entry path
- add the missing entry docs before deeper cleanup
- classify what should be kept as current, kept as reference/archive, or
  quarantined for later cleanup

## Current Truth

Supported current entry flow:

1. [`jarvis/README.md`](</C:/Users/randj/Desktop/project infi/jarvis/README.md>)
2. [`jarvis/jarvis/README.md`](</C:/Users/randj/Desktop/project infi/jarvis/jarvis/README.md>)
3. [`jarvis/jarvis/app/README.md`](</C:/Users/randj/Desktop/project infi/jarvis/jarvis/app/README.md>)
4. [`jarvis/jarvis/tests/README.md`](</C:/Users/randj/Desktop/project infi/jarvis/jarvis/tests/README.md>)
5. [`jarvis/jarvis/data/README.md`](</C:/Users/randj/Desktop/project infi/jarvis/jarvis/data/README.md>)

Operational evidence:

- `pytest.ini` points at `tests`
- `start-jarvis.ps1` and `test-jarvis.ps1` live at the nested project root
- `app/` contains the substantial current runtime/backend lane
- `apps/`, `services/`, and `chat/` already describe themselves as experimental
  or reference lanes

Canonical doctrine note:

- Jarvis memory upgrades are now governed canonically in
  [../contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md](../contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md)
- this doctrine defines the slot-based target law for future memory upgrades
- it should not be misread as proof that the sibling `jarvis` runtime already
  implements the full board/controller/module model exactly as specified

## Missing Entry Docs Identified

These were missing before this pass and are now added:

- `jarvis/README.md`
- `jarvis/jarvis/README.md`
- `jarvis/jarvis/app/README.md`
- `jarvis/jarvis/data/README.md`
- `jarvis/jarvis/jarvis/README.md`
- `jarvis/jarvis/tests/README.md`
- `jarvis/jarvis/Ui jarvis/README.md`

## Keep / Archive / Quarantine

### Keep As Current

- `jarvis/jarvis/app/`
- `jarvis/jarvis/data/`
- `jarvis/jarvis/tests/`
- `jarvis/jarvis/start-jarvis.ps1`
- `jarvis/jarvis/test-jarvis.ps1`
- `jarvis/jarvis/requirements.txt`

### Keep As Reference Or Archived Side Lanes

- `jarvis/jarvis/apps/`
- `jarvis/jarvis/services/`
- `jarvis/jarvis/chat/`
- `jarvis/jarvis/jarvis_v7_sse/`
- `jarvis/jarvis/jarvis-v3/`
- the outer wrapper `.txt` notes in `jarvis/`

### Quarantine Candidates For Deeper Cleanup

- `jarvis/jarvis/jarvis/`
  - nested mirror shell with only `.git` metadata
- `jarvis/jarvis/Ui jarvis/`
  - placeholder lane without a real UI project
- nested-root scratch files:
  - `Untitled-1.py`
  - `docker-compose up --build.py`
  - `docker-compose up --build.txt`
  - `RUN pip install fastapi uvicorn openai p.py`

## Remaining Deeper-Cleanup Questions

- whether the nested `jarvis/` mirror folder should be removed, archived, or
  repopulated intentionally
- whether `Ui jarvis/` should be deleted, archived, or turned back into a real
  UI lane
- whether the loose scratch files at the nested root should be quarantined into
  a residue bucket

## Result Of This Pass

- the `jarvis` sibling now has a clear wrapper entry doc
- the nested project now has a clean root guide instead of a malformed export
- the active runtime, data, tests, and quarantine/reference lanes are now
  documented before any deeper cleanup begins
