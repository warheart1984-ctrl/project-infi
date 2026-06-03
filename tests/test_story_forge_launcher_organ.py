"""Tests for story_forge_launcher_organ."""

from __future__ import annotations

from src.story_forge_launcher_organ import (
    build_story_forge_launcher_status,
    execute_story_forge_launcher_intake,
)


def test_build_status():
    status = build_story_forge_launcher_status()
    assert status["story_forge_launcher_organ_version"] == "story_forge_launcher_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"] == "AAIS-SFLR-01"


def test_execute_intake():
    result = execute_story_forge_launcher_intake({"source_ref": "demo-source.v1"})
    assert result["action"] == "intake"
    assert "ok" in result
