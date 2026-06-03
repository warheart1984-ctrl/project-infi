"""Tests for creative_operator_handoff_organ."""

from __future__ import annotations

from src.creative_operator_handoff_organ import build_creative_operator_handoff_status


def test_build_status():
    status = build_creative_operator_handoff_status()
    assert status["creative_operator_handoff_organ_version"] == "creative_operator_handoff_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
