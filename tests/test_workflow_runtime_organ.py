"""Tests for workflow_runtime_organ."""

from __future__ import annotations

from src.workflow_runtime_organ import build_workflow_runtime_status


def test_build_status():
    status = build_workflow_runtime_status()
    assert status["workflow_runtime_organ_version"] == "workflow_runtime_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

