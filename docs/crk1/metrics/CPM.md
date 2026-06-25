# Continuity Propagation Metric (CPM)

The scalar measure used in Mission #006.

## Definition

The Continuity Propagation Metric (CPM) quantifies whether a steward's judgment improved after replaying preserved calibration lineage.

```
CPM = ΔA = Q_post − Q_pre
```

Where:

- **Q_pre** = pre-assimilation judgment quality
- **Q_post** = post-assimilation judgment quality

## Interpretation

| CPM | Meaning |
|-----|---------|
| CPM > 0 | Improvement |
| CPM = 0 | No change |
| CPM < 0 | Regression |

Continuity is demonstrated if:

```
CPM ≥ τA
```

## Implementation

In `src/crk1/caa1_assimilation.py`, judgment quality Q ∈ [0, 1] is computed from:

- Prediction error (penalty)
- Calibration alignment (bonus)

```python
delta = post.quality() - pre.quality()
```

## Properties

- Model-agnostic
- Task-agnostic
- Lineage-dependent
- Steward-specific
- Empirically measurable

## Why CPM Matters

CPM is the first metric that measures continuity as a **generational** phenomenon, not a structural one.

It is the bridge between:

- CRR-1 (calibration)
- CLG-1 (lineage)
- CAA-1 (assimilation)

## Related

- [TA_SPEC.md](../standards/TA_SPEC.md)
- [CPRP.md](../research/CPRP.md)
