# Lineage Queries (CLG-1)

Standard queries for calibration lineage graph.

Implementation: `CalibrationLineageGraphCLG1` in `src/crk1/calibration_lineage_graph.py`

---

## Q1 — Trace invariant lineage

Given an invariant ID, return all CalibrationEvents that shaped it.

```python
from src.crk1.calibration_lineage_graph import CalibrationLineageGraphCLG1

clg = CalibrationLineageGraphCLG1()
events = clg.trace_invariant_lineage("K6")
```

**Use:** Understand how reality corrected interpretation of an invariant.

---

## Q2 — Steward calibration profile

For steward `S`, list all calibration events and aggregate delta.

```python
profile = clg.steward_calibration_profile("steward_llm")
# profile["event_count"], profile["calibration_delta_sum"], profile["density"]
```

**Use:** Detect insulated stewards (zero events = S-2/S-3 risk).

---

## Q3 — Drift vs correction ratio

Compare interpretive drift index to calibration event density.

```python
ratio = clg.drift_correction_ratio(drift_index=0.05)
# ratio["crr_density"], ratio["ratio"]
```

**Use:** Mission analytics — are corrections keeping pace with drift?

---

## Q4 — Collapse precursor detection

Find stewards with high authority but low calibration density.

```python
precursors = clg.collapse_precursors(
    {"steward_alpha": 0.9, "steward_beta": 0.3},
    calibration_threshold=0.1,
)
```

**Use:** CFM Type IV/V precursor monitoring.

---

## Continuity Graph v2

Unified wire graph + CLG-1 with future-steward reconstruction:

```python
from src.crk1.continuity_graph_v2 import ContinuityGraphV2

graph = ContinuityGraphV2()
graph.ingest_calibration(crr, event)
replay = graph.reconstruct_for_future_steward(crr_id)
```

## Related

[CLG-1 Architecture](../continuity-os/architecture/clg1-lineage.md) · [Mission #005](../continuity-os/missions/mission-005.md)
