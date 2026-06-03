"""Tests for game_front_door_organ."""

from __future__ import annotations

from src.game_front_door_organ import build_game_front_door_status


def test_build_status():
    status = build_game_front_door_status()
    assert status["game_front_door_organ_version"] == "game_front_door_organ.v1"
    assert status["read_only"] is True
