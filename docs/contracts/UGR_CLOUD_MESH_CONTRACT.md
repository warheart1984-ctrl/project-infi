# UGR Cloud Mesh Contract (UGR-CMC-01)

Status: **Phase 2 admitted** — Forge lift single-node cluster.

Authority: `docs/contracts/UGR_RUNTIME_CONTRACT.md`, `docs/programs/UGR_CLOUD_PROGRAM.md`.

## Definition

The UGR cloud mesh decomposes the monolith runtime into governed HTTP services on a
Forge-managed Wolf CoG node (or local docker-compose simulation).

## Services

| Service | Port (default) | Responsibility |
|---|---|---|
| `orchestrator` | 8090 | Gateway; `/v1/deliberate` |
| `policy` | 8091 | Cognitive Bridge + bridge invariant gate |
| `ledger` | 8092 | Unified pattern ledger v0.5 |
| `lane_worker` | 8093 | MLCA parallel lanes |
| `convergence` | 8094 | Deterministic lane merge |
| `ingestion` | 8095 | Curated fetch → ledger pipeline |

## Mesh Config

Path: `deploy/ugr/mesh.local.json` (override with `UGR_MESH_CONFIG`).

Docker path: `deploy/ugr/mesh.docker.json`.

Forge node path: `wolf-cog-os/forge/ugr/mesh.forge-node.json`.

## Deployment Modes

| Mode | Env | Behavior |
|---|---|---|
| `monolith` | default | In-process `UnifiedGovernedRuntime` |
| `distributed` | `UGR_DEPLOYMENT_MODE=distributed` | Mesh clients via HTTP |

## Launch

Local cluster:

```bash
python tools/services/start_ugr_service.py cluster
```

Docker:

```bash
docker compose -f deploy/ugr/docker-compose.yml up
```

Forge pipeline:

```bash
bash wolf-cog-os/forge/scripts/forge-run-pipeline.sh /forge/pipelines/ugr-cloud-cluster.yaml
```

## Security (v2 debt)

Optional shared token: set `UGR_MESH_TOKEN` on all services and clients.

## Verification

```bash
make ugr-cloud-gate
py -3.12 -m pytest tests/test_ugr_cloud.py -q
```
