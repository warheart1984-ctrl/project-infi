"""Tests for state_hygiene_organ."""

from __future__ import annotations

from src.state_hygiene_organ import build_state_hygiene_status


def test_build_status():
    status = build_state_hygiene_status()
    assert status["state_hygiene_organ_version"] == "state_hygiene_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
