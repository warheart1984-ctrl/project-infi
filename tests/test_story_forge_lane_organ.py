"""Tests for story_forge_lane_organ."""

from __future__ import annotations

from src.story_forge_lane_organ import build_story_forge_lane_status


def test_build_status():
    status = build_story_forge_lane_status()
    assert status["story_forge_lane_organ_version"] == "story_forge_lane_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
