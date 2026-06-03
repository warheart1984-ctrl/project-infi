"""Mutation gate tests for MP-OPO-001 on operator_profile_organ."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance_organs.genome_engine import GenomeEngine
from src.governance_organs.mutation_engine import MutationEngine

OPO_INVARIANT = (
    "Profile authority changes require MP-X and post-apply alt7-governed-gate"
)


def test_mp_opo_001_proposal_exists():
    engine = MutationEngine()
    proposals = engine.list_proposals("operator_profile_organ")
    assert any(p.mp_id == "MP-OPO-001" for p in proposals)


def test_mp_opo_001_proposal_post_apply_gate():
    engine = MutationEngine()
    proposal = next(
        p for p in engine.list_proposals("operator_profile_organ") if p.mp_id == "MP-OPO-001"
    )
    assert proposal.post_apply_gate == "operator-profile-gate"


def test_mp_opo_001_verify_passes():
    engine = MutationEngine()
    result = engine.verify("operator_profile_organ", "MP-OPO-001")
    assert result.passed, result.failures


def test_mp_opo_001_apply_and_rollback(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(Path(__file__).resolve().parents[1]))
    engine = MutationEngine()
    genome_path = GenomeEngine.registry().paths["operator_profile_organ"]
    data = json.loads(genome_path.read_text(encoding="utf-8"))
    history = (data.get("mutation") or {}).get("history") or []
    if any(
        entry.get("proposal_id") == "MP-OPO-001" and entry.get("status") == "promoted"
        for entry in history
    ):
        pytest.skip("MP-OPO-001 already promoted in live genome")
    before = genome_path.read_text(encoding="utf-8")
    result = engine.apply(
        "operator_profile_organ",
        "MP-OPO-001",
        invariant=OPO_INVARIANT,
    )
    assert result.passed, result.failures
    data = GenomeEngine.registry().genomes["operator_profile_organ"]
    invariants = (data.get("governance") or {}).get("invariants") or []
    assert OPO_INVARIANT in invariants
    history = (data.get("mutation") or {}).get("history") or []
    assert any(
        entry.get("proposal_id") == "MP-OPO-001" and entry.get("status") == "promoted"
        for entry in history
    )
    engine.rollback("operator_profile_organ", "MP-OPO-001")
    assert genome_path.read_text(encoding="utf-8") == before
