"""Tests for policy_gate_organ."""

from __future__ import annotations

from src.policy_gate_organ import build_policy_gate_status


def test_build_status():
    status = build_policy_gate_status()
    assert status["policy_gate_organ_version"] == "policy_gate_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
