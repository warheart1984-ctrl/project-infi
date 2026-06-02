"""Mutation gate tests for MP-NTP-001 on narrative_trust_pack."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance_organs.genome_engine import GenomeEngine
from src.governance_organs.mutation_engine import MutationEngine

NTP_INVARIANT = "Alt-4 Mutation Engine may append governance invariants via MP-X"


def test_mp_ntp_001_proposal_exists():
    engine = MutationEngine()
    proposals = engine.list_proposals("narrative_trust_pack")
    assert any(p.mp_id == "MP-NTP-001" for p in proposals)


def test_mp_ntp_001_proposal_post_apply_gate():
    engine = MutationEngine()
    proposal = next(p for p in engine.list_proposals("narrative_trust_pack") if p.mp_id == "MP-NTP-001")
    assert proposal.post_apply_gate == "narrative-gate"


def test_mp_ntp_001_verify_passes():
    engine = MutationEngine()
    result = engine.verify("narrative_trust_pack", "MP-NTP-001")
    assert result.passed, result.failures


def test_mp_ntp_001_apply_and_rollback(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(Path(__file__).resolve().parents[1]))
    engine = MutationEngine()
    genome_path = GenomeEngine.registry().paths["narrative_trust_pack"]
    data = json.loads(genome_path.read_text(encoding="utf-8"))
    history = (data.get("mutation") or {}).get("history") or []
    if any(
        entry.get("proposal_id") == "MP-NTP-001" and entry.get("status") == "promoted"
        for entry in history
    ):
        pytest.skip("MP-NTP-001 already promoted in live genome")
    before = genome_path.read_text(encoding="utf-8")
    before_version = (data.get("identity") or {}).get("version")
    result = engine.apply(
        "narrative_trust_pack",
        "MP-NTP-001",
        invariant=NTP_INVARIANT,
    )
    assert result.passed, result.failures
    data = GenomeEngine.registry().genomes["narrative_trust_pack"]
    invariants = (data.get("governance") or {}).get("invariants") or []
    assert NTP_INVARIANT in invariants
    assert (data.get("identity") or {}).get("version") != before_version
    history = (data.get("mutation") or {}).get("history") or []
    assert any(entry.get("proposal_id") == "MP-NTP-001" and entry.get("status") == "promoted" for entry in history)
    engine.rollback("narrative_trust_pack", "MP-NTP-001")
    assert genome_path.read_text(encoding="utf-8") == before
