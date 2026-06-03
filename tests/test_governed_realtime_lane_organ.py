"""Tests for governed_realtime_lane_organ."""

from __future__ import annotations

from src.governed_realtime_lane_organ import build_governed_realtime_lane_status


def test_build_status():
    status = build_governed_realtime_lane_status()
    assert status["governed_realtime_lane_organ_version"] == "governed_realtime_lane_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
