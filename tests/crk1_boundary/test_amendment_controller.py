"""KernelAmendmentController unit tests (CRK-T2 persistence + hysteresis)."""

from __future__ import annotations

import pytest

from src.kernel.amendment_controller import KernelAmendmentController
from src.kernel.governance import Governance


@pytest.fixture(autouse=True)
def _reset_governance() -> None:
    Governance.reset()


def test_below_low_threshold_never_triggers() -> None:
    controller = KernelAmendmentController(theta_high=0.65, theta_low=0.40, persistence_epochs=3)
    for _ in range(10):
        assert controller.decide(0.10) == 0
    assert controller.high_count == 0


def test_single_spike_above_high_does_not_trigger() -> None:
    controller = KernelAmendmentController(theta_high=0.65, theta_low=0.40, persistence_epochs=3)
    assert controller.decide(0.70) == 0
    assert controller.high_count == 1
    assert controller.decide(0.30) == 0
    assert controller.high_count == 0


def test_persistent_high_triggers_after_n_epochs() -> None:
    controller = KernelAmendmentController(theta_high=0.65, theta_low=0.40, persistence_epochs=3)
    assert controller.decide(0.70) == 0
    assert controller.decide(0.72) == 0
    assert controller.decide(0.80) == 1
    assert controller.high_count == 3


def test_hysteresis_resets_when_low() -> None:
    controller = KernelAmendmentController(theta_high=0.65, theta_low=0.40, persistence_epochs=3)
    controller.decide(0.70)
    controller.decide(0.72)
    assert controller.high_count == 2
    controller.decide(0.35)
    assert controller.high_count == 0
