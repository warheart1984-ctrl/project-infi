"""Tests for jarvis_operator_organ."""

from __future__ import annotations

from src.jarvis_operator_organ import build_jarvis_operator_status


def test_build_status():
    status = build_jarvis_operator_status()
    assert status["jarvis_operator_organ_version"] == "jarvis_operator_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("new_execute_authority_via_organ") is False

