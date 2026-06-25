# Assimilation Threshold Standard (τA-Spec)

How to choose the threshold for continuity propagation.

## Purpose

The Assimilation Threshold (τA) defines the minimum improvement required to claim continuity propagation.

## Formal Definition

```
τA ∈ ℝ, τA > 0
```

Continuity is demonstrated if:

```
ΔA ≥ τA
```

## Selection Criteria

τA must satisfy:

### Non-triviality

Must exceed the noise floor of the judgment metric.

### Reproducibility

Independent stewards should achieve ΔA ≥ τA under similar conditions.

### Adversarial Robustness

Threshold must resist gaming or trivial passing.

### Domain Sensitivity

τA must reflect the difficulty of the contradiction class.

## Recommended Defaults

| Task variance | τA |
|---------------|-----|
| Low-variance | 0.02 |
| Medium-variance | 0.05 |
| High-variance | 0.10 |

Mission #006 reference implementation uses **τA = 0.15** for the `physics.fall_time` contradiction class (high error magnitude pre-replay).

## Governance Constraints

- τA cannot be set below the noise floor.
- τA must be documented in the mission manifest.
- τA changes require governance approval.

## Related

- [CPM.md](../metrics/CPM.md)
- [CAA1_VALIDATION_PIPELINE.md](../governance/CAA1_VALIDATION_PIPELINE.md)
