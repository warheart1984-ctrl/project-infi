"""Tests for linguistic_remediation_organ."""

from __future__ import annotations

from src.linguistic_remediation_organ import build_linguistic_remediation_status


def test_build_status():
    status = build_linguistic_remediation_status()
    assert status["linguistic_remediation_organ_version"] == "linguistic_remediation_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
