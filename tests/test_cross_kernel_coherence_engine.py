"""CKCE-1 cross-kernel coherence engine tests."""

from __future__ import annotations

import pytest

from src.continuity.ckce import CKCEThresholds, evaluate_cross_kernel_coherence
from src.continuity.wave_math import WaveSignature


def test_ckce_accepts_coupled_wave_signatures_inside_thresholds() -> None:
    computational = WaveSignature(amplitude=0.55, frequency=0.40, phase=0.95, coherence=0.92, resonance=0.74)
    identity = WaveSignature(amplitude=0.52, frequency=0.39, phase=0.90, coherence=0.91, resonance=0.70)

    result = evaluate_cross_kernel_coherence(
        computational,
        identity,
        thresholds=CKCEThresholds(c_min=0.80, tau=0.80, phi_max=0.10, r_max=0.10),
    )

    assert result.C_comp == pytest.approx(0.92)
    assert result.C_identity == pytest.approx(0.91)
    assert result.C_pair == pytest.approx(0.8372)
    assert result.delta_phi == pytest.approx(0.05)
    assert result.delta_R == pytest.approx(0.04)
    assert result.continuity_ok is True
    assert result.violations == ()


def test_ckce_blocks_when_pair_phase_or_resonance_thresholds_fail() -> None:
    computational = WaveSignature(amplitude=0.70, frequency=0.40, phase=0.95, coherence=0.90, resonance=0.90)
    identity = WaveSignature(amplitude=0.20, frequency=0.30, phase=0.60, coherence=0.70, resonance=0.50)

    result = evaluate_cross_kernel_coherence(
        computational,
        identity,
        thresholds=CKCEThresholds(c_min=0.80, tau=0.80, phi_max=0.10, r_max=0.10),
    )

    assert result.continuity_ok is False
    assert "ckce.identity_coherence_below_min" in result.violations
    assert "ckce.pair_coherence_below_tau" in result.violations
    assert "ckce.phase_drift_exceeds_max" in result.violations
    assert "ckce.resonance_delta_exceeds_max" in result.violations
