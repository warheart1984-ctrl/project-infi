from __future__ import annotations

from nova.law_kernel.evolution_curves import capability_delta


def test_capability_delta_monotonic_in_fitness_and_correctness():
    low = capability_delta(0.2, 0.2)
    mid = capability_delta(0.5, 0.5)
    high = capability_delta(0.9, 0.9)

    assert low <= mid <= high


def test_capability_delta_bounded_between_0_and_1():
    for fitness in [0.0, 0.2, 0.5, 0.8, 1.0, 1.5, -0.5]:
        for correctness in [0.0, 0.3, 0.7, 1.0, 2.0, -1.0]:
            delta = capability_delta(fitness, correctness)
            assert 0.0 <= delta <= 1.0
