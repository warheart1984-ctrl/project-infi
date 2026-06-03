"""Tests for jarvis_protocol_organ."""

from __future__ import annotations

from src.jarvis_protocol_organ import build_jarvis_protocol_status


def test_build_status():
    status = build_jarvis_protocol_status()
    assert status["jarvis_protocol_organ_version"] == "jarvis_protocol_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

