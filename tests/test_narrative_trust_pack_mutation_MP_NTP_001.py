"""Mutation gate tests for MP-NTP-001 on narrative_trust_pack."""

from __future__ import annotations

from pathlib import Path

from src.governance_organs.mutation_engine import MutationEngine


def test_mp_ntp_001_proposal_exists():
    engine = MutationEngine()
    proposals = engine.list_proposals("narrative_trust_pack")
    assert any(p.mp_id == "MP-NTP-001" for p in proposals)


def test_mp_ntp_001_verify_passes():
    engine = MutationEngine()
    result = engine.verify("narrative_trust_pack", "MP-NTP-001")
    assert result.passed, result.failures


def test_mp_ntp_001_apply_and_rollback(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(Path(__file__).resolve().parents[1]))
    engine = MutationEngine()
    result = engine.apply(
        "narrative_trust_pack",
        "MP-NTP-001",
        invariant="Alt-4 Mutation Engine may append governance invariants via MP-X",
    )
    assert result.passed, result.failures
    engine.rollback("narrative_trust_pack", "MP-NTP-001")
