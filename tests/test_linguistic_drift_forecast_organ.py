"""Tests for linguistic_drift_forecast_organ."""

from __future__ import annotations

from src.linguistic_drift_forecast_organ import build_linguistic_drift_forecast_status


def test_build_status():
    status = build_linguistic_drift_forecast_status()
    assert status["linguistic_drift_forecast_organ_version"] == "linguistic_drift_forecast_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
