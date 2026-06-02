# Governed Direct Pipeline — MVP Plan

CISIV stage: concept → implementation target

Status: planned (not yet implemented)

Batch: `barebones-summon-wave-2026-06`

Concept origin: [./GOVERNED_DIRECT_PIPELINE.md](./GOVERNED_DIRECT_PIPELINE.md)

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| module | `src/governed_direct_pipeline.py` | Exists — formalize lane separation contract |
| api | `GET /api/jarvis/pipeline/{turn_id}` | Read-only turn packet trace |
| gate | `make governed-pipeline-gate` | Lane separation + immune hook |
| tests | `tests/test_governed_direct_pipeline.py` | Extend for proof claims |

## 2. Code Artifacts

- `src/api.py` — pipeline inspect route
- `.github/scripts/check-governed-pipeline-governance.py` — gate script
- `docs/runtime/GOVERNED_DIRECT_PIPELINE.md` — active doc on promotion

## 3. Tests

- `tests/test_governed_direct_pipeline.py` — direct vs service lane separation, signal feed validation, immune hook
- Integration: governed turn build with bridge + board context fixtures

## 4. Fixtures

- `fixtures/governed_pipeline/direct-turn.json` — direct_cognitive-only packets
- `fixtures/governed_pipeline/service-lane-turn.json` — service_tools forward/return

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| `make governed-pipeline-gate` | `.github/scripts/check-governed-pipeline-governance.py` | after bridge + memory gates (recommended) |

## 6. Proof Bundle

Target: `docs/proof/platform/GOVERNED_DIRECT_PIPELINE_V1_PROOF.md`

| Claim | Label | Evidence |
|-------|-------|----------|
| Inspect API returns schema-valid turn trace | `none_yet` | Requires implementation |
| Lanes separated on fixture turns | `none_yet` | Requires verification |
| Immune hook present on governed build | `none_yet` | Requires verification |

## 7. Reproduction Commands

```bash
python -m pytest tests/test_governed_direct_pipeline.py -q
make governed-pipeline-gate
make genome-gate
```

## 8. Activation Dependencies

**Existing subsystems required:** `immune_protocol`, `continuity_witness`, **Capability Service Bridge**, **Jarvis Memory Board**

**Order among batch:** **3** — after bridge and memory board

**Rationale:** Pipeline service packets route through the capability bridge; turn context may reference memory board snapshots.
