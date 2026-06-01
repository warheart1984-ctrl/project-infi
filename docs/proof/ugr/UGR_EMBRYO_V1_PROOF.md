# UGR Embryo v1 Proof Bundle

Claim status: **asserted** (local verification only; cross-machine evidence pending)

## Claims

| ID | Claim | Status |
|---|---|---|
| V1-1 | Persistent causal edge log under `causal-graph-v1/edges.jsonl` | asserted |
| V1-2 | Provenance sync from `provenance.jsonl` + claim `evidence_refs` | asserted |
| V1-3 | Region health overlays from `deploy/ugr/regions.json` | asserted |
| V1-4 | Embryo v1 gateway + `/api/ugr/v1/*` routes | asserted |
| V1-5 | Mesh services `causal_graph` (:8100) and `embryo_v1_gateway` (:8101) | asserted |
| V1-6 | Gate `make ugr-causal-graph-gate` | asserted |

## Verification commands

```bash
make ugr-causal-graph-gate
py -3.12 -m pytest tests/test_ugr_causal_graph.py -q
python wolf-cog-os/scripts/validate-ugr-causal-graph-manifest.py --mode fail
```

## Artifacts

| Artifact | Path |
|---|---|
| Causal graph store | `src/ugr/causal_graph/store.py` |
| Provenance materializer | `src/ugr/causal_graph/provenance.py` |
| Region health | `src/ugr/causal_graph/region_health.py` |
| Embryo v1 gateway | `src/ugr/embryo/gateway_v1.py` |
| Config | `deploy/ugr/causal-graph.json`, `deploy/ugr/regions.json` |
| Contract | `docs/contracts/UGR_CAUSAL_GRAPH_V1_CONTRACT.md` |
| Tests | `tests/test_ugr_causal_graph.py` |

## Why

Embryo v0 unified deliberation, ingestion, and in-memory graph queries. v1 adds a **durable causal projection** with provenance linkage and region overlays — the minimum persistent graph backend before an external graph DB (UGR-D2 remainder).

## Open items

- Cross-machine mesh verification not recorded in this bundle
- External graph DB selection (UGR-D2) still open
