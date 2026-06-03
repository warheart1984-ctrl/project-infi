"""Tests for deliberation_organ."""

from __future__ import annotations

from src.deliberation_organ import build_deliberation_status


def test_build_status():
    status = build_deliberation_status()
    assert status["deliberation_organ_version"] == "deliberation_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

