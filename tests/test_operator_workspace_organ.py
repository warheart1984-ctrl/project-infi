"""Tests for operator_workspace_organ."""

from __future__ import annotations

from src.operator_workspace_organ import build_operator_workspace_status


def test_build_status():
    status = build_operator_workspace_status()
    assert status["operator_workspace_organ_version"] == "operator_workspace_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
