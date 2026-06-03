"""Tests for mechanic_handoff_organ."""

from __future__ import annotations

from src.mechanic_handoff_organ import build_mechanic_handoff_status


def test_build_status():
    status = build_mechanic_handoff_status()
    assert status["mechanic_handoff_organ_version"] == "mechanic_handoff_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
