"""Tests for creative_capability_bridge_organ."""

from __future__ import annotations

from src.creative_capability_bridge_organ import build_creative_capability_bridge_status


def test_build_status():
    status = build_creative_capability_bridge_status()
    assert status["creative_capability_bridge_organ_version"] == "creative_capability_bridge_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
