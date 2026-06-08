"""Tests for immune_resilience_organ."""

from __future__ import annotations

from src.immune_resilience_organ import build_immune_resilience_status


def test_build_status():
    status = build_immune_resilience_status()
    assert status["immune_resilience_organ_version"] == "immune_resilience_organ.v1"
    assert status["defensive_only"] is True
    assert status["module_id"] == "AAIS-IR-01"
    assert "defense_generation" in status
    assert "heal_eligible" in status
