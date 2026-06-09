# ARIS standalone service — v1 proof (admission checklist)

Status: **asserted** (MVP service + gate path live; admission criteria partially proven)

Authority: [ARIS_STANDALONE_ADMISSION_SPEC.md](../../contracts/ARIS_STANDALONE_ADMISSION_SPEC.md)

## Admission checklist progress

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Read/analyze/suggest only — no direct runtime mutation | asserted | `aris_service` `/v1/admit` delegates to `build_aris_enforcement` |
| Writes via external suggestion admission | asserted | Same enforcement spine as embedded ARIS |
| Governed genome + `make aris-standalone-gate` | proven | `governance/subsystem_genomes/aris_standalone_service.genome.v1.json`; gate 14 passed (2026-06-08, Python 3.12) |
| Build/runtime split | open | No versioned artifact bundle in v1 sidecar |
| Tenant-scoped auth on service | open | Sidecar has no auth membrane in v1 |
| Proof bundle (this doc + gate output) | partial | See reproduction below |

## Claims

| Claim | Label |
|-------|-------|
| Standalone FastAPI service exposes `/health` and `/v1/admit` | proven |
| Embedded profile remains AAIS authority spine when `ARIS_MODE` unset | proven |
| Client can target standalone via `ARIS_MODE=standalone` | asserted |
| Admission tests (reject without law filter / accept signature-only) | open |

## Reproduction

```powershell
Set-Location e:\project-infi
& "C:\Users\randj\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests/test_aris_standalone_e2e.py::ArisStandaloneSkippedTests -q
make aris-standalone-gate
```

Optional live sidecar (requires FastAPI):

```powershell
$env:ARIS_STANDALONE_E2E = "1"
# uvicorn aris_service:app --port 8765  (separate terminal)
& "C:\Users\randj\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests/test_aris_standalone_e2e.py::test_aris_standalone_health_and_admit -q
```

## Implementation note

MVP code lives in [`aris_service/__init__.py`](../../../aris_service/__init__.py). Full admission per spec §1–5 remains **open** until tenant auth, artifact split, and admission tests are proven.

## Related

- [ARIS_STANDALONE_SERVICE_V1_PROOF.md](./ARIS_STANDALONE_SERVICE_V1_PROOF.md) (legacy stub)
- [SUBSYSTEMS_REMAINING_MAP.md](../../runtime/SUBSYSTEMS_REMAINING_MAP.md)
