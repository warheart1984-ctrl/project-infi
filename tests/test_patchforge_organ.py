"""Tests for patchforge_organ."""

from __future__ import annotations

from src.patchforge_organ import build_patchforge_status


def test_build_status():
    status = build_patchforge_status()
    assert status["patchforge_organ_version"] == "patchforge_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
