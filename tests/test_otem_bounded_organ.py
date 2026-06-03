"""Tests for otem_bounded_organ."""

from __future__ import annotations

from src.otem_bounded_organ import build_otem_bounded_status


def test_build_status():
    status = build_otem_bounded_status()
    assert status["otem_bounded_organ_version"] == "otem_bounded_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
    assert status["proposal_only"] is True
    assert status["execution_allowed"] is False
    assert status["otem_runtime_version"] == "v10_governed"
    assert status["otem_capability_level"] == 10
    assert status["execution_via_workflow_approvals"] is True
