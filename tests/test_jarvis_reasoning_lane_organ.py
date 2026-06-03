"""Tests for jarvis_reasoning_lane_organ."""

from __future__ import annotations

from src.jarvis_reasoning_lane_organ import build_jarvis_reasoning_lane_status


def test_build_status():
    status = build_jarvis_reasoning_lane_status()
    assert status["jarvis_reasoning_lane_organ_version"] == "jarvis_reasoning_lane_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("routing_usurpation") is False
    assert status.get("lane_catalog_only") is True

