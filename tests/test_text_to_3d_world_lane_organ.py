"""Tests for text_to_3d_world_lane_organ."""

from __future__ import annotations

from src.text_to_3d_world_lane_organ import (
    build_text_to_3d_world_lane_status,
    execute_text_to_3d_world_lane_route,
)


def test_build_status():
    status = build_text_to_3d_world_lane_status()
    assert status["text_to_3d_world_lane_organ_version"] == "text_to_3d_world_lane_organ.v1"
    assert status["lane_id"] == "lane.text_to_3d_world"
    assert status["read_only"] is True
    assert status["route_status"] == "configured"
    assert status["aais_live_lane"] is True


def test_execute_route_blocks_without_operator_ack(tmp_path):
    result = execute_text_to_3d_world_lane_route(
        {"prompt": "make a small 3d relic game", "seed": "s1"},
        root=tmp_path,
    )

    assert result["ok"] is False
    assert result["claim_label"] == "blocked"
    assert "operator_ack" in result["message"]


def test_execute_route_generates_world_pack(tmp_path):
    result = execute_text_to_3d_world_lane_route(
        {
            "prompt": "make a moonlit 3d archive game with keys",
            "seed": "s1",
            "session_id": "session-route",
            "operator_ack": True,
        },
        root=tmp_path,
    )

    assert result["ok"] is True
    assert result["route_status"] == "configured"
    assert result["aais_live_lane"] is True
    assert result["proposal_only"] is False
    assert result["world_spec_ref"].endswith("world.spec.json")
    assert result["playable_ref"].endswith("index.html")
