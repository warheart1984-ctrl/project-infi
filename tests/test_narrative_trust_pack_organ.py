"""Tests for narrative_trust_pack_organ."""

from __future__ import annotations

from src.narrative_trust_pack_organ import build_narrative_trust_pack_status


def test_build_status():
    status = build_narrative_trust_pack_status()
    assert status["narrative_trust_pack_organ_version"] == "narrative_trust_pack_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
