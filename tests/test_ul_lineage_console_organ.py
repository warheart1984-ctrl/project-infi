"""Tests for ul_lineage_console_organ."""

from __future__ import annotations

from src.ul_lineage_console_organ import build_ul_lineage_console_status


def test_build_status():
    status = build_ul_lineage_console_status()
    assert status["ul_lineage_console_organ_version"] == "ul_lineage_console_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
