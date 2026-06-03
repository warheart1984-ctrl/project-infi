"""Tests for speakers_lane_organ."""

from __future__ import annotations

from src.speakers_lane_organ import build_speakers_lane_status


def test_build_status():
    status = build_speakers_lane_status()
    assert status["speakers_lane_organ_version"] == "speakers_lane_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
