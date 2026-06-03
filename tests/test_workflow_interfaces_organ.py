"""Tests for workflow_interfaces_organ."""

from __future__ import annotations

from src.workflow_interfaces_organ import build_workflow_interfaces_status


def test_build_status():
    status = build_workflow_interfaces_status()
    assert status["workflow_interfaces_organ_version"] == "workflow_interfaces_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
