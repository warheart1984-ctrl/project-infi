# UGR Causal Graph v1 Contract

Authority: `docs/programs/UGR_CLOUD_PROGRAM.md`  
Canonical claim backend: JSONL (`collective-pattern-ledger/**/claims.jsonl`)  
Persistent causal log: JSONL (`collective-pattern-ledger/causal-graph-v1/edges.jsonl`)

## Scope

Embryo v1 adds a **persistent causal graph backend** on top of graph index v1:

- Append-only causal edge log derived from provenance links and claim `evidence_refs`
- Subject/object chain edges (`caused_by`) for linked claims
- Region health overlays from `deploy/ugr/regions.json`
- Query surfaces: causal walk, provenance lookup, region health

JSONL remains canonical. The causal graph is a derived, rebuildable projection.

## Enablement

| Variable | Value | Effect |
|---|---|---|
| `UGR_CAUSAL_GRAPH_ENABLED` | `1` | Use `CausalGraphStore` in `PatternLedgerStore` (includes graph index) |
| `UGR_CAUSAL_GRAPH_CONFIG` | path | Override `deploy/ugr/causal-graph.json` |
| `UGR_REGIONS_CONFIG` | path | Override `deploy/ugr/regions.json` |

When causal graph is enabled, graph index queries remain available through the same store.

## API surfaces

### Monolith (`src/api.py`)

| Route | Method | Purpose |
|---|---|---|
| `/api/ugr/v1/health` | GET | Embryo v1 health + region overlay |
| `/api/ugr/v1/causal/query` | POST | Causal walk from `claim_id` |
| `/api/ugr/v1/provenance` | POST | Provenance edges for `claim_id` |
| `/api/ugr/v1/regions/health` | GET | Region health snapshot |
| `/api/ugr/v1/causal/rebuild` | POST | Rebuild causal graph from JSONL |

### Mesh

| Service | Port (local) | Factory |
|---|---|---|
| `causal_graph` | 8100 | `create_causal_graph_app` |
| `embryo_v1_gateway` | 8101 | `create_embryo_v1_gateway_app` |

## Invariants

1. Causal edges are append-only; rebuild may add missing edges but never mutates canonical claim JSONL
2. Tenant scope filtering applies on causal walks (global + tenant overlay)
3. Region health is advisory overlay only — does not bypass Cognitive Bridge or invariants
4. All v1 gateway responses include `embryo.gateway_surface = v1` and `claim_status = asserted` until proof bundle attached

## Verification

```bash
make ugr-causal-graph-gate
```

Evidence: `docs/proof/ugr/UGR_EMBRYO_V1_PROOF.md`

## Debt

- **UGR-D2:** External graph DB selection remains open; v1 closes persistent JSONL causal layer only
