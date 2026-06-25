# CLG-1 — Calibration Lineage Graph

Structural memory of corrigibility across time.

## Definition

```
G = (V, E)
```

### Vertices

| Node type | Source |
|-----------|--------|
| CalibrationEvent | Derived from CRR-1 |
| Steward | Stewardship registry |
| Invariant | K-entries |
| DecisionCluster | Aggregated GRR-1s |
| RealityChannel | Evidence paths |

### Edges

| Edge | Meaning |
|------|---------|
| `corrects` | Calibration → decision cluster |
| `updates` | Calibration → invariant |
| `performed_by` | Calibration → steward |
| `inherits_from` | Steward → steward handoff |
| `influences` | Calibration → calibration |

## Ingestion rules

1. Every validated CRR-1 **must** produce one CalibrationEvent vertex
2. `performed_by` links to `steward_id`
3. Append-only — corrections add nodes; never delete

## Standard queries

| Query | Purpose |
|-------|---------|
| **Q1** | Trace invariant lineage |
| **Q2** | Steward calibration profile |
| **Q3** | Drift vs correction ratio |
| **Q4** | Collapse precursor detection |

Details: [Lineage Queries](../../reference/lineage-queries.md)

## Implementation

- Module: `src/crk1/calibration_lineage_graph.py`
- Graph v2: `src/crk1/continuity_graph_v2.py`

## Spec

[`CLG1_CALIBRATION_LINEAGE_GRAPH`](../crk1/continuity-os/CLG1_CALIBRATION_LINEAGE_GRAPH.md)
