"""Tests for perception_gateway_organ."""

from __future__ import annotations

from src.perception_gateway_organ import build_perception_gateway_status


def test_build_status():
    status = build_perception_gateway_status()
    assert status["perception_gateway_organ_version"] == "perception_gateway_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

