# UGR Platform Scale Contract (Phase 4)

Authority: `META_ARCHITECT_LAWBOOK.md`, `docs/contracts/UGR_RUNTIME_CONTRACT.md`.

## Scope

Phase 4 adds multi-tenant ledger overlays, graph shard routing, and shadow-runtime cognition CI/CD without replacing constitutional bridge law.

## Tenant overlays

- Tenant registry: `deploy/ugr/tenants.json`
- Canonical tenant ids: `global`, `tenant:<name>`
- Overlay reads merge **global shard + tenant shard** when `overlay_global=true`
- Cross-tenant reads are forbidden — tenant B must never see tenant A private claims

Enable sharded ledger in monolith:

```bash
export UGR_PLATFORM_ENABLED=1
export UGR_TENANTS_CONFIG=deploy/ugr/tenants.json
export UGR_GRAPH_SHARDS_CONFIG=deploy/ugr/graph-shards.json
```

## Graph sharding

- Shard map: `deploy/ugr/graph-shards.json`
- Storage backend v0: JSONL per shard under `.runtime/collective-pattern-ledger/shards/<shard_id>/`
- Debt **UGR-D2** remains: no external graph DB yet; sharding is a routing layer only

## Shadow runtime CI/CD

- Promotion policy: `deploy/ugr/cognition-promotion.json`
- Shadow runtime uses a sibling runtime dir (`<runtime>-shadow`) with identical deliberation inputs
- Decisions: `promote`, `reject`, `human_review` based on belief signature match rate and status parity

## Mesh service

| Service | Port | Role |
|---|---|---|
| platform | 8096 | tenant overlay queries, shadow eval, CI/CD |

Routes:

- `GET /v1/platform/tenants`
- `GET /v1/platform/shards`
- `POST /v1/platform/ledger/query`
- `POST /v1/platform/shadow-eval`
- `POST /v1/platform/cicd/evaluate`

## API (monolith)

- `GET /api/ugr/platform/tenants`
- `POST /api/ugr/platform/shadow-eval`
- `POST /api/ugr/platform/cicd/evaluate`

## Verification

```bash
make ugr-platform-gate
```

Claim status: **asserted** until gate evidence is recorded in a proof bundle.
