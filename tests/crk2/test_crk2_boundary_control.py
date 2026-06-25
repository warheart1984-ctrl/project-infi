"""CRK-T2 outer-loop control law tests."""

from __future__ import annotations

import pytest

from src.continuity.crk2_boundary_control import (
    BoundaryControlConfig,
    BoundaryTelemetry,
    OuterLoopState,
    compute_insufficiency,
    decide_amendment,
    smooth_insufficiency,
    step_outer_loop,
    update_kernel_version,
)
from src.kernel.governance import Governance


@pytest.fixture(autouse=True)
def _reset_governance() -> None:
    Governance.reset()


def test_insufficiency_weighted_sum() -> None:
    cfg = BoundaryControlConfig(weights=(0.5, 0.1, 0.1, 0.2, 0.1))
    telemetry = BoundaryTelemetry(
        semantic_duplication=1.0,
        replay_complexity=0.0,
        invariant_violations=0.0,
        fitness_divergence=0.0,
        contract_redundancy=0.0,
    )
    assert compute_insufficiency(telemetry, cfg) == pytest.approx(0.5)


def test_ema_smoothing() -> None:
    smoothed = smooth_insufficiency(1.0, 0.0, alpha=0.3)
    assert smoothed == pytest.approx(0.3)
    again = smooth_insufficiency(1.0, smoothed, alpha=0.3)
    assert again == pytest.approx(0.51)


def test_amendment_requires_consecutive_epochs() -> None:
    cfg = BoundaryControlConfig(
        consecutive_epochs=3,
        theta_high=0.45,
        theta_low=0.3,
        alpha=0.5,
    )
    state = OuterLoopState()
    high = BoundaryTelemetry(
        semantic_duplication=1.0,
        replay_complexity=1.0,
        invariant_violations=1.0,
        fitness_divergence=1.0,
        contract_redundancy=1.0,
    )

    for _ in range(2):
        state, report = step_outer_loop(state, high, config=cfg)
        assert report["amendment_signal"] == 0

    state, report = step_outer_loop(state, high, config=cfg)
    assert report["amendment_signal"] == 1


def test_hysteresis_clears_below_theta_low() -> None:
    cfg = BoundaryControlConfig(consecutive_epochs=2, theta_high=0.5, theta_low=0.4)
    state = OuterLoopState(consecutive_high_epochs=2, amendment_signal=1)
    u, streak = decide_amendment(0.3, state, cfg)
    assert u == 0
    assert streak == 0


def test_kernel_version_updates_only_when_ratified() -> None:
    assert update_kernel_version(1, 1, False) == 1
    assert update_kernel_version(1, 1, True) == 2
    assert update_kernel_version(2, 0, True) == 2


def test_ratification_bumps_kernel_and_resets_amendment() -> None:
    cfg = BoundaryControlConfig(consecutive_epochs=1, theta_high=0.4, theta_low=0.1, alpha=1.0)
    high = BoundaryTelemetry(
        semantic_duplication=1.0,
        replay_complexity=1.0,
        invariant_violations=1.0,
        fitness_divergence=1.0,
        contract_redundancy=1.0,
    )
    state, report = step_outer_loop(OuterLoopState(), high, ratified=True, config=cfg)
    assert report["amendment_ratified"] is True
    assert report["kernel_version"] == 2
    assert state.amendment_signal == 0
