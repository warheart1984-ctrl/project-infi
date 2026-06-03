"""Tests for wolf_rehydration_organ."""

from __future__ import annotations

from src.wolf_rehydration_organ import build_wolf_rehydration_status


def test_build_status():
    status = build_wolf_rehydration_status()
    assert status["wolf_rehydration_organ_version"] == "wolf_rehydration_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

