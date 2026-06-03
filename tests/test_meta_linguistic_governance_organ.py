"""Tests for meta_linguistic_governance_organ."""

from __future__ import annotations

from src.meta_linguistic_governance_organ import build_meta_linguistic_governance_status


def test_build_status():
    status = build_meta_linguistic_governance_status()
    assert status["meta_linguistic_governance_organ_version"] == "meta_linguistic_governance_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
