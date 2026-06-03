"""Tests for operator_health_sentinel_organ."""

from __future__ import annotations

from src.operator_health_sentinel_organ import build_operator_health_sentinel_organ_status


def test_build_status():
    status = build_operator_health_sentinel_organ_status()
    assert status["operator_health_sentinel_organ_version"] == "operator_health_sentinel_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
