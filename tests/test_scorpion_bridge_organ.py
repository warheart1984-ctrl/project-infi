"""Tests for scorpion_bridge_organ."""

from __future__ import annotations

from src.scorpion_bridge_organ import build_scorpion_bridge_status


def test_build_status():
    status = build_scorpion_bridge_status()
    assert status["scorpion_bridge_organ_version"] == "scorpion_bridge_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
