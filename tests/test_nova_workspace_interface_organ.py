"""Tests for nova_workspace_interface_organ."""

from __future__ import annotations

from src.nova_workspace_interface_organ import build_nova_workspace_interface_status


def test_build_status():
    status = build_nova_workspace_interface_status()
    assert status["nova_workspace_interface_organ_version"] == "nova_workspace_interface_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
