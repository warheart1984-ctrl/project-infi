"""Tests for tier-0 cosmogenic engine."""

from __future__ import annotations

import numpy as np

from iogs.tier_0.cosmogenic_engine import (
    estimate_10be_concentration,
    run_tier0_cosmogenic,
    spectrum_to_cr_proxy,
)
from iogs.tier_0.t0_receiver import CosmicRayData
from iogs.tier_0.t0_sensor_registry import get_t0_sensor_class


def test_ntia_adapter_registered():
    assert get_t0_sensor_class("NTIAAdapter") is not None


def test_estimate_10be_uses_adapter():
    freq = np.logspace(6, 9, 50)
    flux = 1e-12 * (freq / freq.max()) ** -2
    conc = estimate_10be_concentration(freq, flux, material_context="l7_spectral")
    assert conc > 0


def test_run_tier0_from_pair():
    freq = np.linspace(1e6, 1e9, 32)
    flux = np.random.default_rng(0).uniform(1e-15, 1e-12, size=32)
    run = run_tier0_cosmogenic((freq, flux), source_label="test")
    assert run.tier == 0
    assert run.output.concentration_10be_equiv is not None
    assert run.spectral_proxy is not None
    assert run.spectral_proxy.layer7_method == "l7_8_alpha_beta_gamma"


def test_run_tier0_enriches_cosmic_ray_data():
    freq = np.array([1e6, 1e7, 1e8])
    flux = np.array([1e-12, 1e-13, 1e-14])
    cr = CosmicRayData(energy=freq, flux=flux)
    run = run_tier0_cosmogenic(cr)
    assert run.output.concentration_10be_equiv is not None


def test_spectrum_to_cr_proxy_fields():
    freq = np.logspace(7, 8, 10)
    flux = np.ones(10) * 1e-12
    sp = spectrum_to_cr_proxy(freq, flux)
    assert sp.alpha is not None
    assert sp.layer7_calibration_uncertainty_pct > 0
