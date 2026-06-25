"""
Tier 0 cosmogenic pipeline using layer-0ae T0-promoted sensor adapters and Layer-7 validator.
Input: spectrum or (E, F), optional manual α/β/γ → 10Be(cm⁻² yr⁻¹)-equivalent via Layer-7 calibration (L7-8).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Union

import numpy as np

from iogs.tier_0.cosmogenic_calibration import get_calibration_uncertainty_pct, iso_correct_10be_equiv
from iogs.tier_0.ntia_spectrum_loader import SpectrumLike, to_ntia_spectrum
from iogs.tier_0.t0_receiver import CosmicRayData
from iogs.tier_0.t0_sensor import (
    compute_alpha_beta_gamma_from_features,
    feature_10be_concentration_proxy,
    feature_spectral_slope,
    feature_suery_interval,
)
from iogs.tier_0.t0_sensor_registry import get_t0_sensor_class


# ---------------------------------------------------------------------------
# Provenance: T0-promoted sensor adapters (Layer-0AE — constitutional binding)
# ---------------------------------------------------------------------------


def estimate_10be_concentration(
    frequency: Union[np.ndarray, Sequence[float]],
    flux: Union[np.ndarray, Sequence[float]],
    *,
    material_context: Optional[str] = None,
) -> float:
    """Proxy 10Be surface concentration (atoms g⁻¹) via registered T0 sensor or legacy feature.

    Prefer ``get_t0_sensor_class("NTIAAdapter")`` when the registry exposes it; fall back to
    ``feature_10be_concentration_proxy`` otherwise. ``material_context`` selects the dominant
    feature branch (e.g. ``l7_spectral``, ``nuclear``) per ``CBIDProtocolRouter``.
    """
    w = np.asarray(frequency, dtype=np.float64)
    f = np.asarray(flux, dtype=np.float64)
    adapter_cls = get_t0_sensor_class("NTIAAdapter")
    features: Dict[str, Any] = {
        "spectral_slope": feature_spectral_slope(w, f),
        **feature_suery_interval(w, f),
    }
    if adapter_cls is not None and hasattr(adapter_cls, "compute_features"):
        features = adapter_cls.compute_features(w, f)
    return float(
        feature_10be_concentration_proxy(
            features,
            material_context=material_context or "l7_spectral",
        )
    )


# ---------------------------------------------------------------------------
# Adapter: spectrum → α, β, γ → 10Be-equiv
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SpectralCrProxy:
    """Tier 0 cosmogenic proxy from EM spectrum (no ¹⁰Be chemistry)."""

    alpha: float
    beta: float
    gamma: float
    concentration_proxy: float
    concentration_10be_equiv_atoms_per_g_yr: float
    layer7_method: str
    layer7_calibration_uncertainty_pct: float


def spectrum_to_abg(
    frequency: Union[np.ndarray, Sequence[float]],
    flux: Union[np.ndarray, Sequence[float]],
) -> Dict[str, float]:
    """Map (frequency, flux) to α, β, γ via spectral features."""
    w = np.asarray(frequency, dtype=np.float64)
    f = np.asarray(flux, dtype=np.float64)
    features: Dict[str, Any] = {"spectral_slope": feature_spectral_slope(w, f)}
    return compute_alpha_beta_gamma_from_features(features)


def spectrum_to_cr_proxy(
    frequency: Union[np.ndarray, Sequence[float]],
    flux: Union[np.ndarray, Sequence[float]],
    *,
    layer7_mukin: float = 4.0,
    layer7_phi_mu_coeff: float = 0.001,
    material_context: Optional[str] = None,
) -> SpectralCrProxy:
    """
    Full pipeline: spectrum → α,β,γ → feature proxy → Layer-7 ``alpha_beta_gamma_to_10be`` in cm⁻² yr⁻¹
    → ``iso_correct_10be_equiv`` (atoms g⁻¹ yr⁻¹ equivalent for consistency).
    """
    abg = spectrum_to_abg(frequency, flux)
    proxy = estimate_10be_concentration(
        frequency, flux, material_context=material_context
    )
    from iogs.tier_0.cosmogenic_calibration import alpha_beta_gamma_to_10be

    cal = alpha_beta_gamma_to_10be(
        abg["alpha"],
        abg["beta"],
        abg["gamma"],
        mukin_override=layer7_mukin,
        phi_mu_coeff=layer7_phi_mu_coeff,
    )
    conc_l7 = cal["10be_concentration"]
    conc_iso = iso_correct_10be_equiv(
        float(np.mean(flux)) if flux is not None and len(flux) else 1.0,
        std_calibration=cal.get("calibration_std", 0.15),
    )
    conc = 0.5 * (float(conc_l7) * 1e-6 + conc_iso)
    return SpectralCrProxy(
        alpha=abg["alpha"],
        beta=abg["beta"],
        gamma=abg["gamma"],
        concentration_proxy=proxy,
        concentration_10be_equiv_atoms_per_g_yr=conc,
        layer7_method="l7_8_alpha_beta_gamma",
        layer7_calibration_uncertainty_pct=get_calibration_uncertainty_pct(),
    )


# ---------------------------------------------------------------------------
# Tier 0 engine surface
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Tier0CosmogenicRun:
    output: CosmicRayData
    spectral_proxy: Optional[SpectralCrProxy]
    source: str
    tier: int = 0


def run_tier0_cosmogenic(
    spectrum_or_pair: Union[SpectrumLike, Mapping[str, Any], tuple, CosmicRayData],
    *,
    source_label: str = "tier0",
    material_context: Optional[str] = None,
    layer7_mukin: float = 4.0,
    layer7_phi_mu_coeff: float = 0.001,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tier0CosmogenicRun:
    """
    Accepts:
      - NTIASpectrum / dict / (E, F) / existing CosmicRayData
    Produces CosmicRayData with ``concentration_10be_equiv`` and optional spectral ABG proxy.
    """
    meta = dict(metadata or {})
    meta.setdefault("tier", 0)

    if isinstance(spectrum_or_pair, CosmicRayData):
        cr = spectrum_or_pair
        if cr.concentration_10be_equiv is None and cr.energy is not None and cr.flux is not None:
            sp = spectrum_to_cr_proxy(
                cr.energy,
                cr.flux,
                layer7_mukin=layer7_mukin,
                layer7_phi_mu_coeff=layer7_phi_mu_coeff,
                material_context=material_context,
            )
            cr = CosmicRayData(
                energy=cr.energy,
                flux=cr.flux,
                timestamp=cr.timestamp,
                quality=cr.quality,
                concentration_10be_equiv=sp.concentration_10be_equiv_atoms_per_g_yr,
                provenance={**(cr.provenance or {}), "tier0_proxy": sp},
            )
            return Tier0CosmogenicRun(output=cr, spectral_proxy=sp, source=source_label)
        return Tier0CosmogenicRun(
            output=spectrum_or_pair, spectral_proxy=None, source=source_label
        )

    spec = to_ntia_spectrum(spectrum_or_pair)
    sp = spectrum_to_cr_proxy(
        spec.frequency_hz,
        spec.power,
        layer7_mukin=layer7_mukin,
        layer7_phi_mu_coeff=layer7_phi_mu_coeff,
        material_context=material_context,
    )
    cr = CosmicRayData(
        energy=spec.frequency_hz,
        flux=spec.power,
        timestamp=spec.timestamp_utc,
        concentration_10be_equiv=sp.concentration_10be_equiv_atoms_per_g_yr,
        quality={"tier0": True, "units": spec.units},
        provenance={
            "source": source_label,
            "ntia": spec.source_path or spec.title,
            "abg": {"alpha": sp.alpha, "beta": sp.beta, "gamma": sp.gamma},
            **meta,
        },
    )
    return Tier0CosmogenicRun(output=cr, spectral_proxy=sp, source=source_label)


def run_tier0_from_ntia_path(
    path: Union[str, Path],
    **kwargs: Any,
) -> Tier0CosmogenicRun:
    """Load NTIA CSV/Parquet and run tier-0 cosmogenic pipeline."""
    from iogs.tier_0.ntia_spectrum_loader import load_spectrum_file

    spec = load_spectrum_file(path)
    return run_tier0_cosmogenic(spec, source_label=str(path), **kwargs)
