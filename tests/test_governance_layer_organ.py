"""Tests for governance_layer_organ."""

from __future__ import annotations

from src.governance_layer_organ import build_governance_layer_status


def test_build_status():
    status = build_governance_layer_status()
    assert status["governance_layer_organ_version"] == "governance_layer_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

