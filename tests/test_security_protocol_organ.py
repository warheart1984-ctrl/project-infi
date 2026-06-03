"""Tests for security_protocol_organ."""

from __future__ import annotations

from src.security_protocol_organ import build_security_protocol_status


def test_build_status():
    status = build_security_protocol_status()
    assert status["security_protocol_organ_version"] == "security_protocol_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

