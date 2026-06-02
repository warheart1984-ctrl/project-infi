"""Mutation gate tests for MP-ALO-001 on adaptive_lane_organ."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance_organs.genome_engine import GenomeEngine
from src.governance_organs.mutation_engine import MutationEngine

LANE_INVARIANT = (
    "Lane DNA mutations require MP-X, fabric re-validation, and post-apply wake"
)


def test_mp_alo_001_proposal_exists():
    engine = MutationEngine()
    proposals = engine.list_proposals("adaptive_lane_organ")
    assert any(p.mp_id == "MP-ALO-001" for p in proposals)


def test_mp_alo_001_lane_delta_fields():
    engine = MutationEngine()
    proposal = next(p for p in engine.list_proposals("adaptive_lane_organ") if p.mp_id == "MP-ALO-001")
    assert proposal.mutation_kind == "lane_dna"
    assert proposal.post_apply_wake is True
    assert proposal.post_apply_gate == "alt6-governed-gate"


def test_mp_alo_001_verify_passes():
    engine = MutationEngine()
    result = engine.verify("adaptive_lane_organ", "MP-ALO-001")
    assert result.passed, result.failures


def test_mp_alo_001_apply_and_rollback(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(Path(__file__).resolve().parents[1]))
    engine = MutationEngine()
    genome_path = GenomeEngine.registry().paths["adaptive_lane_organ"]
    data = json.loads(genome_path.read_text(encoding="utf-8"))
    history = (data.get("mutation") or {}).get("history") or []
    if any(
        entry.get("proposal_id") == "MP-ALO-001" and entry.get("status") == "promoted"
        for entry in history
    ):
        pytest.skip("MP-ALO-001 already promoted in live genome")
    before = genome_path.read_text(encoding="utf-8")
    result = engine.apply(
        "adaptive_lane_organ",
        "MP-ALO-001",
        invariant=LANE_INVARIANT,
    )
    assert result.passed, result.failures
    data = GenomeEngine.registry().genomes["adaptive_lane_organ"]
    lanes = (data.get("governance") or {}).get("operator_lanes") or []
    operator_lane = next(lane for lane in lanes if lane.get("lane_id") == "operator")
    assert "audit_lane_mutation" in operator_lane.get("capabilities", [])
    engine.rollback("adaptive_lane_organ", "MP-ALO-001")
    assert genome_path.read_text(encoding="utf-8") == before
