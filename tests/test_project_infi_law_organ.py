"""Tests for project_infi_law_organ."""

from __future__ import annotations

from src.project_infi_law_organ import build_project_infi_law_status


def test_build_status():
    status = build_project_infi_law_status()
    assert status["project_infi_law_organ_version"] == "project_infi_law_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

