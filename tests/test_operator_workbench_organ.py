"""Tests for operator_workbench_organ."""

from __future__ import annotations

from src.operator_workbench_organ import build_operator_workbench_status


def test_build_status():
    status = build_operator_workbench_status()
    assert status["operator_workbench_organ_version"] == "operator_workbench_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("proposal_only") is True

