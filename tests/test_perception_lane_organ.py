"""Tests for perception_lane_organ."""

from __future__ import annotations

from src.perception_lane_organ import build_perception_lane_status


def test_build_status():
    status = build_perception_lane_status()
    assert status["perception_lane_organ_version"] == "perception_lane_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

