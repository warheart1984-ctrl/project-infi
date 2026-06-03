"""Mutation gate tests for MP-OCCF-001 on operator_cognition_coherence_fabric."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance_organs.genome_engine import GenomeEngine
from src.governance_organs.mutation_engine import MutationEngine

OCCF_INVARIANT = (
    "Coherence fabric genome mutations require MP-X and post-apply alt7-governed-gate"
)


def test_mp_occf_001_proposal_exists():
    engine = MutationEngine()
    proposals = engine.list_proposals("operator_cognition_coherence_fabric")
    assert any(p.mp_id == "MP-OCCF-001" for p in proposals)


def test_mp_occf_001_proposal_post_apply_gate():
    engine = MutationEngine()
    proposal = next(
        p
        for p in engine.list_proposals("operator_cognition_coherence_fabric")
        if p.mp_id == "MP-OCCF-001"
    )
    assert proposal.post_apply_gate == "alt7-governed-gate"


def test_mp_occf_001_verify_passes():
    engine = MutationEngine()
    result = engine.verify("operator_cognition_coherence_fabric", "MP-OCCF-001")
    assert result.passed, result.failures


def test_mp_occf_001_apply_and_rollback(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(Path(__file__).resolve().parents[1]))
    engine = MutationEngine()
    genome_path = GenomeEngine.registry().paths["operator_cognition_coherence_fabric"]
    data = json.loads(genome_path.read_text(encoding="utf-8"))
    history = (data.get("mutation") or {}).get("history") or []
    if any(
        entry.get("proposal_id") == "MP-OCCF-001" and entry.get("status") == "promoted"
        for entry in history
    ):
        pytest.skip("MP-OCCF-001 already promoted in live genome")
    before = genome_path.read_text(encoding="utf-8")
    result = engine.apply(
        "operator_cognition_coherence_fabric",
        "MP-OCCF-001",
        invariant=OCCF_INVARIANT,
    )
    assert result.passed, result.failures
    data = GenomeEngine.registry().genomes["operator_cognition_coherence_fabric"]
    invariants = (data.get("governance") or {}).get("invariants") or []
    texts = [
        entry.get("text") if isinstance(entry, dict) else str(entry)
        for entry in invariants
    ]
    assert OCCF_INVARIANT in texts
    history = (data.get("mutation") or {}).get("history") or []
    assert any(
        entry.get("proposal_id") == "MP-OCCF-001" and entry.get("status") == "promoted"
        for entry in history
    )
    engine.rollback("operator_cognition_coherence_fabric", "MP-OCCF-001")
    assert genome_path.read_text(encoding="utf-8") == before
