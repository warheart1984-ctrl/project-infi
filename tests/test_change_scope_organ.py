"""Tests for change_scope_organ."""

from __future__ import annotations

from src.change_scope_organ import build_change_scope_status


def test_build_status():
    status = build_change_scope_status()
    assert status["change_scope_organ_version"] == "change_scope_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
