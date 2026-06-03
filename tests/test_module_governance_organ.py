"""Tests for module_governance_organ."""

from __future__ import annotations

from src.module_governance_organ import build_module_governance_status


def test_build_status():
    status = build_module_governance_status()
    assert status["module_governance_organ_version"] == "module_governance_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
