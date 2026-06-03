"""Tests for naming_protocol_organ."""

from __future__ import annotations

from src.naming_protocol_organ import build_naming_protocol_status


def test_build_status():
    status = build_naming_protocol_status()
    assert status["naming_protocol_organ_version"] == "naming_protocol_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
