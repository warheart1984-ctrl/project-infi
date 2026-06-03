"""Tests for aais_ul_substrate_organ."""

from __future__ import annotations

from src.aais_ul_substrate_organ import build_aais_ul_substrate_status


def test_build_status():
    status = build_aais_ul_substrate_status()
    assert status["aais_ul_substrate_organ_version"] == "aais_ul_substrate_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

