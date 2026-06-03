"""Tests for cortex_arcs_organ."""

from __future__ import annotations

from src.cortex_arcs_organ import build_cortex_arcs_status


def test_build_status():
    status = build_cortex_arcs_status()
    assert status["cortex_arcs_organ_version"] == "cortex_arcs_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

