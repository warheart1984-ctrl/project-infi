"""Tests for text_game_to_video_organ."""

from __future__ import annotations

from src.text_game_to_video_organ import build_text_game_to_video_status


def test_build_status():
    status = build_text_game_to_video_status()
    assert status["text_game_to_video_organ_version"] == "text_game_to_video_organ.v1"
    assert status["read_only"] is True
