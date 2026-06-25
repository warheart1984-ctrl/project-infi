from __future__ import annotations


def capability_delta(evidence_fitness: float, correctness: float) -> float:
    """Fitness-weighted capability evolution curve (sqrt of product)."""
    f = max(0.0, min(evidence_fitness, 1.0))
    c = max(0.0, min(correctness, 1.0))
    return (f * c) ** 0.5
