# Tri-Core ↔ Nexus OS Decoupling Prep

**Status:** Preparation (ports + config seams; full split not yet deployed)  
**Scope:** `project-infi` governed constitutional spine

## Problem

Four different concepts share overlapping names:

| Bucket | ID | Location | Role |
|--------|-----|----------|------|
| **tri_core.routing** | `tri_core` | `src/cog_runtime/nova_face.py` | Thalamus cognitive routing (Face → Cortex → Tri-Core binding) |
| **tri_core.governance** | `@aaes-os/tri-core-protocol` | `aaes-os/packages/tri-core-protocol/` | Patch proposer/reviewer/approver workflow (TS only) |
| **nexus.execution** | `nexus` | `src/aaes_os/modules/nexus.py` | AAES execution module + JSONL ledger (spine step 4) |
| **nexusos.continuity** | `nexusos` | `urg-wt/src/fos/integrations/nexusos.py` | FOS civilization wire (not wired into spine yet) |

**Do not conflate** thalamus `tri_core` with AAES module `nexus` or FOS thread `nexusos`.

See also: `docs/architecture/AAES_OS_UCR_MAPPING.md` (§ Tri-Core — two distinct concepts).

## Current spine (coupled)

```
make_governed_mission
  Nova (law_eval)
  → URG (urg_receipt)
  → AAES (aaes_receipt)     module_id from GOVERNED_AAES_MODULE_ID
  → Nexus (nexus_event)     GOVERNED_NEXUS_RECORD_MODE
  → persistence             optional GOVERNED_NEXUSOS_FOS_EXPORT
```

## Decoupling seams (implemented)

### 1. Ports (`src/governed/ports.py`)

- `LawEvalPort`, `UrgMissionPort`, `AaesExecutePort`
- `NexusRecordPort` — execution observability only
- `NexusOsContinuityPort` — optional FOS export

### 2. Adapters (`src/governed/adapters.py`)

- `LocalNexusRecordAdapter` — default JSONL ledger
- `NullNexusRecordAdapter` — `GOVERNED_NEXUS_RECORD_MODE=disabled`
- `NullNexusOsContinuityAdapter` / `UrgWtNexusOsContinuityAdapter` stub

### 3. Config (`src/governed/config.py`)

| Env var | Default | Purpose |
|---------|---------|---------|
| `GOVERNED_TRI_CORE_ROUTING_AUTHORITY` | `tri_core` | DAR-Z routing lane (must stay `tri_core` until kernel validation loosens) |
| `GOVERNED_AAES_MODULE_ID` | `nexus` | AAES module at step 3 |
| `GOVERNED_NEXUS_RECORD_MODE` | `in_process` | `disabled` skips Nexus ledger |
| `GOVERNED_NEXUSOS_FOS_EXPORT` | off | Enable FOS export hook |
| `GOVERNED_*_IN_PROCESS` | on | HTTP vs in-process per stage |

Schema: `schemas/governed/spine_boundary.v1.json`

## Deployment patterns (target)

### A. Monolith (today)

All stages in-process; default config.

### B. Nexus execution as separate service

```
GOVERNED_AAES_IN_PROCESS=0
GOVERNED_NEXUS_RECORD_MODE=disabled   # record on remote Nexus service
AAIS_BASE_URL=https://aais.example
```

AAES remote service owns `nexus.execution`; spine receives receipt only.

### C. Tri-Core routing only (no Nexus ledger)

```
GOVERNED_NEXUS_RECORD_MODE=disabled
```

Spine still runs; `nexus_event.status=skipped`.

### D. NexusOS FOS export (future)

```
GOVERNED_NEXUSOS_FOS_EXPORT=1
```

Calls `NexusOsContinuityPort` from persistence — wire to `urg-wt` `ingest_urg_mission_receipt`.

## Next steps (not yet done)

1. HTTP adapter for `NexusRecordPort` (remote ledger API)
2. Wire `UrgWtNexusOsContinuityAdapter` to real FOS kernel or urg-wt package
3. Extract `make_governed_mission` stage injection (swap ports in tests/CI)
4. E2E with all `GOVERNED_*_IN_PROCESS=0`
5. Rename TS ops-console vs Python `nexus/ops_console` in launch checklist
6. Versioned payloads under `schemas/governed/` for law_eval, urg_receipt, aaes_receipt, nexus_event

## Tests

```bash
pytest tests/test_governed_boundary_ports.py -q
pytest tests/test_e2e_governed_mission.py -q
```

## Evidence

- Ports/adapters: `src/governed/ports.py`, `src/governed/adapters.py`
- Boundary in persistence trace: `persistence["spine_boundary"]`
