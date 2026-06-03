"""Tests for reasoning_executive_organ."""

from __future__ import annotations

from src.reasoning_executive_organ import build_reasoning_executive_status


def test_build_status():
    status = build_reasoning_executive_status()
    assert status["reasoning_executive_organ_version"] == "reasoning_executive_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("routing_usurpation") is False
    assert status.get("executive_authority") == "jarvis"

