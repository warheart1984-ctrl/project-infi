"""Tests for patch_apply_organ."""

from __future__ import annotations

from src.patch_apply_organ import build_patch_apply_status


def test_build_status():
    status = build_patch_apply_status()
    assert status["patch_apply_organ_version"] == "patch_apply_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
