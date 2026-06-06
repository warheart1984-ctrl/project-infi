# Workflow Family Organs v1 — Proof Packet

Status: **prototype proof**

CISIV stage: **structure → implementation**

## Scope

Phase 1 and Phase 2 of the AAIS Organs layer (workflow-family composition):

- Six workflow-family organs in `governance/workflow_family_registry.v1.json`
- Registry engine: `src/workflow_family_registry.py`
- Operator API: `GET /api/operator/organs`, `GET /api/operator/organs/<family_id>`
- Governed chain executor: `src/workflow_chain_executor.py`
- Chain API: `POST /api/operator/workflows/<id>/execute`
- Operator UI: Organs tab in `frontend/src/pages/OperatorPlugins.jsx`

## Validation commands

```bash
make workflow-family-gate
python -m pytest tests/test_workflow_family_registry.py tests/test_workflow_chain_executor.py -q
python .github/scripts/check-brain-layer-governance.py
python -m pytest tests/test_brain_layer_runtime.py -q
```

## API evidence

| Endpoint | Expected |
|----------|----------|
| `GET /api/operator/organs` | Returns 6 families with readiness rollups |
| `GET /api/operator/organs/knowledge_work` | Returns abilities, chains, libraries |
| `GET /api/operator/brain` | Returns Nova Cortex bounded Brain-layer status |
| `POST /api/operator/workflows/research_brief/execute` | Returns chain_run envelope when ready + approved |
| `GET /api/operator/workflows/<id>/runs/<run_id>` | Returns run status |

## Governance evidence

| Artifact | Path |
|----------|------|
| Family schema | `schemas/aais_workflow_family.v1.json` |
| Family registry | `governance/workflow_family_registry.v1.json` |
| Parent genome | `governance/subsystem_genomes/workflow_family_registry.genome.v1.json` |
| Anatomical map | `docs/runtime/AAIS_ANATOMICAL_LAYERS.md` |
| Brain adapter | `src/brain_layer_runtime.py` |
| Gate | `make workflow-family-gate` |

## Invariants asserted

1. Six families always present: knowledge, business, creative, data, ops, personal
2. Family readiness rolls up from libraries + bundles without inventing plugs
3. Chain execution reuses `plug_adapter_runtime.execute()` — no parallel path
4. High-risk chains require `operator_approved: true`
5. Per-step and chain receipts emitted to Operator Decision Ledger
6. OTEM enrichment attaches `suggested_workflow_family` (proposal-only)
7. Nova Cortex Brain layer remains `wired_bounded` and cannot self-authorize execution

## Known limitations

- Linear chain only — no DAG branching
- Families with `pending_plug` steps remain `partial`/`missing`
- Brain layer is wired to Nova Cortex as bounded cognition; autonomous self-routing and multi-agent
  delegation remain explicitly not built
