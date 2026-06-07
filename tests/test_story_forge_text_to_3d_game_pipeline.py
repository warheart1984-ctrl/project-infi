"""Tests for the deterministic Story Forge text-to-3D game pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "external" / "story_forge" / "src"))
from story_forge.text_to_3d_game_pipeline import build_text_to_3d_world_pack


def test_build_world_pack_is_deterministic(tmp_path):
    first = build_text_to_3d_world_pack(
        prompt="Build a moonlit archive game where the player finds three keys.",
        seed="fixed-seed",
        session_id="session-a",
        output_root=tmp_path,
    )
    second = build_text_to_3d_world_pack(
        prompt="Build a moonlit archive game where the player finds three keys.",
        seed="fixed-seed",
        session_id="session-a",
        output_root=tmp_path,
    )

    assert first["ok"] is True
    assert first["world_id"] == second["world_id"]
    assert first["world_spec"] == second["world_spec"]
    assert first["scene_manifest"] == second["scene_manifest"]
    assert first["playable_manifest"]["entrypoint"] == "index.html"


def test_world_pack_contains_engine_neutral_specs_and_playable(tmp_path):
    result = build_text_to_3d_world_pack(
        prompt="Create a desert tower platform game with a relic and a hazard.",
        seed="tower-seed",
        session_id="session-b",
        output_root=tmp_path,
    )

    world_pack = result["world_pack_path"]
    assert (world_pack / "world.spec.json").is_file()
    assert (world_pack / "gameplay.spec.json").is_file()
    assert (world_pack / "scene.manifest.json").is_file()
    assert (world_pack / "playable_manifest.json").is_file()
    assert (world_pack / "lane_receipt.json").is_file()
    assert (world_pack / "index.html").is_file()

    world_spec = json.loads((world_pack / "world.spec.json").read_text(encoding="utf-8"))
    assert world_spec["schema_version"] == "story_forge.game_world.v1"
    assert world_spec["engine_targets"] == ["threejs_static", "engine_neutral_json"]
    assert world_spec["player"]["kind"] == "explorer"
    assert world_spec["objectives"]


def test_empty_prompt_is_blocked(tmp_path):
    result = build_text_to_3d_world_pack(
        prompt="   ",
        seed="empty",
        session_id="session-c",
        output_root=tmp_path,
    )

    assert result["ok"] is False
    assert result["claim_label"] == "blocked"
    assert "prompt required" in result["message"]
