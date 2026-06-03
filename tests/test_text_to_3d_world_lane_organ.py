"""Tests for text_to_3d_world_lane_organ."""

from __future__ import annotations

from src.text_to_3d_world_lane_organ import build_text_to_3d_world_lane_status


def test_build_status():
    status = build_text_to_3d_world_lane_status()
    assert status["text_to_3d_world_lane_organ_version"] == "text_to_3d_world_lane_organ.v1"
    assert status["lane_id"] == "lane.text_to_3d_world"
    assert status["read_only"] is True
