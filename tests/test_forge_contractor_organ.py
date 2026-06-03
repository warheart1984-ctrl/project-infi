"""Tests for forge_contractor_organ."""

from __future__ import annotations

from src.forge_contractor_organ import build_forge_contractor_status


def test_build_status():
    status = build_forge_contractor_status()
    assert status["forge_contractor_organ_version"] == "forge_contractor_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("proposal_only") is True
    assert status.get("auto_approve_allowed") is False

