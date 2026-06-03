"""Tests for human_voice_extraction_organ."""

from __future__ import annotations

from src.human_voice_extraction_organ import build_human_voice_extraction_status


def test_build_status():
    status = build_human_voice_extraction_status()
    assert status["human_voice_extraction_organ_version"] == "human_voice_extraction_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
