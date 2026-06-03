"""Tests for continuity_substrate_organ."""

from __future__ import annotations

from src.continuity_substrate_organ import build_continuity_substrate_status


def test_build_status():
    status = build_continuity_substrate_status()
    assert status["continuity_substrate_organ_version"] == "continuity_substrate_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

