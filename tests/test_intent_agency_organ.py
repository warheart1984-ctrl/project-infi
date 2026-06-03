"""Tests for intent_agency_organ."""

from __future__ import annotations

from src.intent_agency_organ import build_intent_agency_status


def test_build_intent_agency_status():
    status = build_intent_agency_status()
    assert status["intent_agency_organ_version"] == "intent_agency_organ.v1"
    assert status["agency_note"]
    assert status["active_commitment_count"] >= 1
    assert status["agency_claim_posture"] in {"asserted", "proven", "rejected"}
    assert status["read_only"] is True
