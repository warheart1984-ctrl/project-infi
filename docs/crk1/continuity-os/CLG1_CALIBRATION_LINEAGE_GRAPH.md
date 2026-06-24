# CLG-1 — Calibration Lineage Graph

**Version:** 1.0  
**Status:** Normative  
**Purpose:** Linked calibration events across time — preserves corrigibility lineage

---

## 1. Graph definition

\[
G = (V, E)
\]

### Vertices \(V\)

| Node type | Source |
|-----------|--------|
| **CalibrationEvent** | Derived from CRR-1 |
| **Steward** | Stewardship Registry |
| **Invariant** | K-entries (K0–K15, K-∞, KΩ) |
| **DecisionCluster** | Aggregated GRR-1s |

### Edges \(E\)

| Edge | From → To | Meaning |
|------|-----------|---------|
| `corrects` | CalibrationEvent → DecisionCluster | Calibration invalidated/adjusted a decision cluster |
| `updates` | CalibrationEvent → Invariant | Calibration shifted invariant interpretation |
| `performed_by` | CalibrationEvent → Steward | Who underwent or initiated calibration |
| `inherits_from` | Steward → Steward | Lineage handoff |
| `influences` | CalibrationEvent → CalibrationEvent | Downstream calibration effects |

---

## 2. Ingestion rules

1. Every validated **CRR-1** MUST produce one **CalibrationEvent** vertex.
2. `performed_by` MUST link to `steward_id` from CRR-1 metadata.
3. `context_id` MAY link to GRR-1 or DecisionCluster.
4. Handoff events (SHP) add `inherits_from` edges between Steward nodes.

Append-only: calibration nodes are never deleted; corrections add new nodes and edges.

---

## 3. Standard queries

### Q1 — Lineage of a correction

Given a present invariant state, trace all CalibrationEvents that shaped it.

```
trace_invariant_lineage(invariant_id) → [CalibrationEvent, ...]
```

### Q2 — Steward calibration profile

For steward `S`, list all CalibrationEvents undergone or initiated.

```
steward_calibration_profile(steward_id) → { events, calibration_delta_sum, density }
```

### Q3 — Drift vs correction

Compare invariant drift over time vs calibration density in CLG-1.

```
drift_correction_ratio(epoch_range) → { drift_index, crr_density, ratio }
```

### Q4 — Collapse precursor detection

Identify graph regions where:

- Decisions accumulate **without** corresponding CalibrationEvents
- Steward nodes with **high authority** have **low calibration degree**

Used by CFM for Type IV and Type V precursors.

---

## 4. Relationship to other artifacts

| Artifact | Role in CLG-1 |
|----------|---------------|
| CRR-1 | Primary node source |
| GRR-1 | DecisionCluster aggregation |
| D-3 Seal | External verification node (optional Steward event) |
| KCR | May link `updates` to Invariant nodes |

**Schema:** `fixtures/crk1/calibration_reconstruction_receipt.schema.json`

---

## 5. Implementation status (CRK-1 v1.0)

| Capability | Status |
|------------|--------|
| CRR-1 wire schema | Normative |
| CLG-1 storage / API | Specified; `continuity_graph` TBD |
| Explorer / VR rendering | Via Continuity API graph endpoints |

See: [CONTINUITY_OS_RUNTIME_SPEC.md](CONTINUITY_OS_RUNTIME_SPEC.md), [../roadmap/CRK1_GRAPH_DATA_CONTRACT.md](../roadmap/CRK1_GRAPH_DATA_CONTRACT.md)
