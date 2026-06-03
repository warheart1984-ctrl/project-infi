"""Tests for media_processor_bridge_organ."""

from __future__ import annotations

from src.media_processor_bridge_organ import (
    build_media_processor_bridge_status,
    execute_media_processor_bridge,
)


def test_build_status():
    status = build_media_processor_bridge_status()
    assert status["media_processor_bridge_organ_version"] == "media_processor_bridge_organ.v1"
    assert status["module_id"] == "AAIS-MPB-01"
    assert status["processor_seeds"]["audio_processor"] is True


def test_execute_audio_processor():
    result = execute_media_processor_bridge("audio_processor", {"action": "inspect"})
    assert result["ok"] is True
    assert result["processor"] == "audio_processor"
