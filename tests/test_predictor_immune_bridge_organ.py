"""Tests for predictor_immune_bridge_organ."""

from __future__ import annotations

from src.predictor_immune_bridge_organ import build_predictor_immune_bridge_status


def test_build_status():
    status = build_predictor_immune_bridge_status()
    assert status["predictor_immune_bridge_organ_version"] == "predictor_immune_bridge_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
