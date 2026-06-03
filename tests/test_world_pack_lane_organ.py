"""Tests for world_pack_lane_organ."""

from __future__ import annotations

from src.world_pack_lane_organ import build_world_pack_lane_status


def test_build_status():
    status = build_world_pack_lane_status()
    assert status["world_pack_lane_organ_version"] == "world_pack_lane_organ.v1"
    assert status["read_only"] is True
