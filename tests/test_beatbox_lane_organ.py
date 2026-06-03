"""Tests for beatbox_lane_organ."""

from __future__ import annotations

from src.beatbox_lane_organ import build_beatbox_lane_status


def test_build_status():
    status = build_beatbox_lane_status()
    assert status["beatbox_lane_organ_version"] == "beatbox_lane_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
