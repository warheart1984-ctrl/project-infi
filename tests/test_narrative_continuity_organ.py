"""Tests for narrative_continuity_organ."""

from __future__ import annotations

from src.narrative_continuity_organ import build_narrative_continuity_status


def test_build_narrative_continuity_status():
    status = build_narrative_continuity_status()
    assert status["narrative_continuity_organ_version"] == "narrative_continuity_organ.v1"
    assert status["continuity_score"] >= 1.0
    assert status["story_persistence_rate"] >= 1.0
    assert status["continuity_complete"] is True
    assert status["read_only"] is True
