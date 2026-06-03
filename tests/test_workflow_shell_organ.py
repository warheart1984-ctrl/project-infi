"""Tests for workflow_shell_organ."""

from __future__ import annotations

from src.workflow_shell_organ import build_workflow_shell_status


def test_build_status():
    status = build_workflow_shell_status()
    assert status["workflow_shell_organ_version"] == "workflow_shell_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

