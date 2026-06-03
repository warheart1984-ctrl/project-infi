"""Tests for mission_board_organ."""

from __future__ import annotations

from src.mission_board_organ import build_mission_board_status


def test_build_status():
    status = build_mission_board_status()
    assert status["mission_board_organ_version"] == "mission_board_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
