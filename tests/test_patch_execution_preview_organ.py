"""Tests for patch_execution_preview_organ."""

from __future__ import annotations

from src.patch_execution_preview_organ import build_patch_execution_preview_status


def test_build_status():
    status = build_patch_execution_preview_status()
    assert status["patch_execution_preview_organ_version"] == "patch_execution_preview_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
