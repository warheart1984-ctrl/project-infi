"""Mutation gate tests for MP-SE-001 on safety_envelope_organ."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance_organs.genome_engine import GenomeEngine
from src.governance_organs.mutation_engine import MutationEngine

SE_INVARIANT = (
    "Envelope threshold mutations require MP-X and post-apply alt7-governed-gate"
)


def test_mp_se_001_proposal_exists():
    engine = MutationEngine()
    proposals = engine.list_proposals("safety_envelope_organ")
    assert any(p.mp_id == "MP-SE-001" for p in proposals)


def test_mp_se_001_verify_passes():
    engine = MutationEngine()
    result = engine.verify("safety_envelope_organ", "MP-SE-001")
    assert result.passed, result.failures


def test_mp_se_001_apply_and_rollback(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(Path(__file__).resolve().parents[1]))
    engine = MutationEngine()
    genome_path = GenomeEngine.registry().paths["safety_envelope_organ"]
    data = json.loads(genome_path.read_text(encoding="utf-8"))
    history = (data.get("mutation") or {}).get("history") or []
    if any(
        entry.get("proposal_id") == "MP-SE-001" and entry.get("status") == "promoted"
        for entry in history
    ):
        pytest.skip("MP-SE-001 already promoted in live genome")
    before = genome_path.read_text(encoding="utf-8")
    result = engine.apply(
        "safety_envelope_organ",
        "MP-SE-001",
        invariant=SE_INVARIANT,
    )
    assert result.passed, result.failures
    data = GenomeEngine.registry().genomes["safety_envelope_organ"]
    invariants = (data.get("governance") or {}).get("invariants") or []
    assert SE_INVARIANT in invariants
    engine.rollback("safety_envelope_organ", "MP-SE-001")
    assert genome_path.read_text(encoding="utf-8") == before
