"""Tests for output_integrity_organ."""

from __future__ import annotations

from src.output_integrity_organ import build_output_integrity_status


def test_build_status():
    status = build_output_integrity_status()
    assert status["output_integrity_organ_version"] == "output_integrity_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

