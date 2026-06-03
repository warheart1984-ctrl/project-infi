"""Tests for verification_gate_organ."""

from __future__ import annotations

from src.verification_gate_organ import build_verification_gate_status


def test_build_status():
    status = build_verification_gate_status()
    assert status["verification_gate_organ_version"] == "verification_gate_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
