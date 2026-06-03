"""Tests for cognitive_bridge_organ."""

from __future__ import annotations

from src.cognitive_bridge_organ import build_cognitive_bridge_status


def test_build_status():
    status = build_cognitive_bridge_status()
    assert status["cognitive_bridge_organ_version"] == "cognitive_bridge_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
