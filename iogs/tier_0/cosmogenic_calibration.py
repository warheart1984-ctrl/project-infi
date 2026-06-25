"""Layer-7 cosmogenic calibration (L7-8 α/β/γ → ¹⁰Be equivalent)."""

from __future__ import annotations

import math
from typing import Any, Dict

_DEFAULT_CALIBRATION_UNCERTAINTY_PCT = 15.0


def get_calibration_uncertainty_pct() -> float:
    return _DEFAULT_CALIBRATION_UNCERTAINTY_PCT


def alpha_beta_gamma_to_10be(
    alpha: float,
    beta: float,
    gamma: float,
    *,
    mukin_override: float = 4.0,
    phi_mu_coeff: float = 0.001,
) -> Dict[str, Any]:
    """
    Map spectral ABG proxies to ¹⁰Be surface concentration (atoms cm⁻² yr⁻¹ class).
    Simplified L7-8 closure for tier-0 pipeline (not full CRONUS).
    """
    phi_mu = phi_mu_coeff * max(abs(alpha), 1e-12)
    mukin = mukin_override * (1.0 + 0.1 * abs(beta))
    conc = mukin * phi_mu * (1.0 + 0.05 * abs(gamma)) * 1e4
    std = conc * (_DEFAULT_CALIBRATION_UNCERTAINTY_PCT / 100.0)
    return {
        "10be_concentration": float(conc),
        "calibration_std": float(std),
        "mukin": float(mukin),
        "phi_mu": float(phi_mu),
    }


def iso_correct_10be_equiv(
    flux_mean: float,
    *,
    std_calibration: float = 0.15,
) -> float:
    """Isotope-style correction from mean spectral flux."""
    base = max(flux_mean, 1e-30)
    return float(math.log10(base + 1.0) * (1.0 - std_calibration))
