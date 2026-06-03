"""Tests for linguistic_predictive_governance_organ."""

from __future__ import annotations

from src.linguistic_predictive_governance_organ import build_linguistic_predictive_governance_status


def test_build_status():
    status = build_linguistic_predictive_governance_status()
    assert status["linguistic_predictive_governance_organ_version"] == "linguistic_predictive_governance_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
