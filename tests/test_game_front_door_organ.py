"""Tests for game_front_door_organ."""

from __future__ import annotations

from src.game_front_door_organ import build_game_front_door_status, execute_game_front_door_admit


def test_build_status():
    status = build_game_front_door_status()
    assert status["game_front_door_organ_version"] == "game_front_door_organ.v1"
    assert status["read_only"] is True


def test_game_front_door_routes_prompt_to_text_to_3d_lane(tmp_path):
    result = execute_game_front_door_admit(
        {
            "session_id": "game-session",
            "operator_ack": True,
            "prompt": "create a tower game with a relic",
            "seed": "front-door-seed",
        },
        root=tmp_path,
    )

    assert result["ok"] is True
    assert result["front_door_active"] is True
    assert result["lane_result"]["organ"] == "text_to_3d_world_lane_organ"
    assert result["lane_result"]["world_pack_ref"]
