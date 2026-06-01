# UGR Cloud Super-LLM Embryo v0 Contract

Authority: `META_ARCHITECT_LAWBOOK.md`, `docs/contracts/UGR_RUNTIME_CONTRACT.md`, `docs/contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md`.

## Purpose

Embryo v0 is the first operable governed super-LLM organism surface: one gateway ingress over orchestrator, model pool, ingestion, pattern ledger, invariants, immune runtime, and Cloud Forge rails.

## Components

| Component | Surface | Status in v0 |
|---|---|---|
| Orchestrator | UGR runtime / mesh `:8090` | wired |
| Model pool | `src/ugr/embryo/model_pool.py`, mesh `:8098` | proposal-only slots |
| Ingestion | governed pipeline, gateway `/v0/ingest` | wired |
| Pattern ledger | unified v0.5 + optional graph index | wired |
| Invariants | bridge + lane gates | wired |
| Immune runtime | bridge immune controller | wired |
| API gateway | `/api/ugr/v0/*`, mesh `:8099` | wired |

## Model pool

Config: `deploy/ugr/model-pool.json`

Resolution inputs:

- Cloud Forge `rail_decision.rail`
- Cloud Forge `cognition_plan.model_tier`
- LLM lane `governed_llm` envelope (if present)
- Tenant scope + law signals (`required_proof` caps tier)

Outputs: `model_pool` block on every deliberation response with `proposal_only: true`, `execution_authority: none`, `generation_overrides.temperature: 0`.

## Gateway surface v0

Monolith:

- `GET /api/ugr/v0/health`
- `POST /api/ugr/v0/deliberate`
- `POST /api/ugr/v0/ingest`
- `GET /api/ugr/v0/ingest/sources`
- `POST /api/ugr/v0/graph/query`
- `POST /api/ugr/v0/shadow-eval`

Mesh embryo gateway (`:8099`): `/v1/embryo/*` mirrors the above.

Every gateway response includes an `embryo` envelope:

```json
{
  "embryo_id": "aais.ugr.embryo",
  "embryo_version": "0.1",
  "gateway_surface": "v0",
  "operation": "deliberate",
  "trace_id": "...",
  "rail_decision": {},
  "model_pool": {},
  "component_health": {},
  "claim_status": "asserted"
}
```

## Non-negotiables

1. Bridge remains lawful ingress for deliberation.
2. Model pool never grants execution authority in v0.
3. Provider I/O stays behind governed LLM seam (proposal-only).
4. JSONL ledger remains canonical write path.

## Verification

```bash
make ugr-embryo-gate
```

Claim status: **asserted** until proof bundle evidence is attached.
