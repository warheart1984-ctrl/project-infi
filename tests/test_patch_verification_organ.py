"""Tests for patch_verification_organ."""

from __future__ import annotations

from src.patch_verification_organ import build_patch_verification_status


def test_build_status():
    status = build_patch_verification_status()
    assert status["patch_verification_organ_version"] == "patch_verification_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
