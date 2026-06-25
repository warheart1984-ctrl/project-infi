"""Tier-0 promoted sensor features (Layer-0AE binding, no legacy import)."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np


def feature_spectral_slope(
    frequency: np.ndarray,
    flux: np.ndarray,
    **_kwargs: Any,
) -> float:
    w = np.log10(np.maximum(np.asarray(frequency, dtype=np.float64), 1e-30))
    f = np.log10(np.maximum(np.asarray(flux, dtype=np.float64), 1e-30))
    if len(w) < 2:
        return 0.0
    return float(np.gradient(f, w).mean())


def feature_suery_interval(
    frequency: np.ndarray,
    flux: np.ndarray,
    **_kwargs: Any,
) -> Dict[str, float]:
    f = np.asarray(flux, dtype=np.float64)
    if f.size == 0:
        return {"suery_low": 0.0, "suery_high": 1.0}
    p10, p90 = np.percentile(f, [10, 90])
    return {"suery_low": float(p10), "suery_high": float(p90)}


def compute_alpha_beta_gamma_from_features(features: Dict[str, Any]) -> Dict[str, float]:
    slope = float(features.get("spectral_slope", 0.0))
    suery_low = float(features.get("suery_low", 0.0))
    suery_high = float(features.get("suery_high", 1.0))
    spread = max(suery_high - suery_low, 1e-12)
    return {
        "alpha": slope,
        "beta": spread,
        "gamma": float(features.get("suery_high", 0.0)),
    }


def feature_10be_concentration_proxy(
    features: Dict[str, Any],
    *,
    material_context: str | None = None,
) -> float:
    abg = compute_alpha_beta_gamma_from_features(features)
    base = abs(abg["alpha"]) + 0.5 * abg["beta"] + 0.1 * abs(abg["gamma"])
    if material_context and "nuclear" in material_context.lower():
        return base * 1.2
    return base


class NTIAAdapter:
    """T0-promoted NTIA spectrum adapter."""

    name = "NTIAAdapter"

    @staticmethod
    def compute_features(frequency: np.ndarray, flux: np.ndarray) -> Dict[str, Any]:
        return {
            "spectral_slope": feature_spectral_slope(frequency, flux),
            **feature_suery_interval(frequency, flux),
        }
