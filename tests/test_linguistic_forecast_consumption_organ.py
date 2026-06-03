"""Tests for linguistic_forecast_consumption_organ."""

from __future__ import annotations

from src.linguistic_forecast_consumption_organ import build_linguistic_forecast_consumption_status


def test_build_status():
    status = build_linguistic_forecast_consumption_status()
    assert status["linguistic_forecast_consumption_organ_version"] == "linguistic_forecast_consumption_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
