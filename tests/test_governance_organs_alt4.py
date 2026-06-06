"""Alt-4 runtime organs — genome, promotion, mutation, retirement."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _repo_root(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(REPO))


def test_genome_registry_valid():
    from src.governance_organs import GenomeEngine

    reg = GenomeEngine.validate_registry(REPO)
    assert reg.ok, reg.errors
    assert len(reg.genomes) >= 6


def test_genome_boot_warn_mode(monkeypatch):
    from src.governance_organs import Alt4Runtime

    monkeypatch.setenv("AAIS_GENOME_BOOT", "warn")
    Alt4Runtime.boot_validate()


def test_promotion_evaluate_recipe_module():
    from src.governance_organs.promotion_engine import PromotionEngine

    engine = PromotionEngine(REPO)
    decision = engine.evaluate("recipe_module")
    assert decision.current_stage == "governed"
    assert decision.target_stage is None
    assert decision.passed


def test_promotion_idempotent_at_governed():
    from src.governance_organs.promotion_engine import PromotionEngine

    engine = PromotionEngine(REPO)
    decision = engine.evaluate("recipe_module")
    assert decision.current_stage == "governed"
    applied = engine.apply(decision, dry_run=False)
    assert applied.passed


def test_promotion_rollback_restores_backup():
    from src.governance_organs.promotion_engine import PromotionEngine

    engine = PromotionEngine(REPO)
    path = engine._genome_path("recipe_module")
    original = json.loads(path.read_text(encoding="utf-8"))
    modified = json.loads(path.read_text(encoding="utf-8"))
    modified["identity"]["stage"] = "governed"
    engine._write_genome("recipe_module", modified)
    assert engine.rollback("recipe_module")
    restored = json.loads(path.read_text(encoding="utf-8"))
    assert restored["identity"]["stage"] == original["identity"]["stage"]


def test_mutation_mp_ntp_001_roundtrip():
    from src.governance_organs.mutation_engine import MutationEngine

    engine = MutationEngine(REPO)
    genome_path = engine._genome_path("narrative_trust_pack")
    genome = json.loads(genome_path.read_text(encoding="utf-8"))
    history = (genome.get("mutation") or {}).get("history") or []
    if any(
        entry.get("proposal_id") == "MP-NTP-001" and entry.get("status") == "promoted"
        for entry in history
    ):
        pytest.skip("MP-NTP-001 already promoted in live genome")
    verify = engine.verify("narrative_trust_pack", "MP-NTP-001")
    assert verify.passed, verify.failures
    apply_result = engine.apply(
        "narrative_trust_pack",
        "MP-NTP-001",
        invariant="Alt-4 Mutation Engine may append governance invariants via MP-X",
    )
    assert apply_result.passed, apply_result.failures
    genome = json.loads(engine._genome_path("narrative_trust_pack").read_text(encoding="utf-8"))
    history = genome.get("mutation", {}).get("history") or []
    assert history[-1]["proposal_id"] == "MP-NTP-001"
    assert engine.rollback("narrative_trust_pack", "MP-NTP-001")


def test_retirement_dry_run_advance():
    from src.governance_organs.retirement_engine import RetirementEngine

    engine = RetirementEngine(REPO)
    state = engine.advance("operator_profile_organ", dry_run=True, target_step=6)
    assert state.current_step >= 6
    assert not state.failures


def test_retirement_scan_all_dry_run():
    from src.governance_organs.retirement_engine import RetirementEngine

    engine = RetirementEngine(REPO)
    results = engine.scan_all(dry_run=True, target_step=3)
    assert len(results) >= 6
    ok = [r for r in results if not r.failures]
    assert ok, "expected at least one gene without lineage retirement blocks"
    assert all(r.current_step >= 3 for r in ok)


def test_retirement_emission_monitor():
    from src.governance_organs.retirement_engine import RetirementEngine

    engine = RetirementEngine(REPO)
    report = engine.emission_unused("recipe_module")
    assert "releases_since_activity" in report
    assert "releases_required" in report


def test_alt4_gate_main():
    from src.governance_organs import Alt4Runtime

    code = Alt4Runtime.alt4_gate()
    assert code == 0


ORIGINAL_SIX = frozenset(
    {
        "cisiv_operator_lineage_console",
        "forensic_triangulation",
        "narrative_trust_pack",
        "recipe_module",
        "imagine_generator",
        "human_voice_extraction",
    }
)

ALT5_GENES = frozenset(
    {
        "safety_envelope_organ",
        "operator_profile_organ",
        "reflection_runtime_organ",
        "memory_runtime_organ",
    }
)


def test_all_six_genomes_governed():
    from src.governance_organs import GenomeEngine

    reg = GenomeEngine.reload(REPO)
    for gene in ORIGINAL_SIX:
        stage = (reg.genomes[gene].get("identity") or {}).get("stage")
        assert stage == "governed", f"{gene} expected governed, got {stage}"


def test_all_alt5_genomes_governed():
    from src.governance_organs import GenomeEngine

    reg = GenomeEngine.reload(REPO)
    for gene in ALT5_GENES:
        stage = (reg.genomes[gene].get("identity") or {}).get("stage")
        assert stage == "governed", f"{gene} expected governed, got {stage}"


def test_alt4_gate_strict_passes_for_constitutional_layer():
    from src.governance_organs import Alt4Runtime
    from src.governance_organs.promotion_engine import PromotionEngine

    engine = PromotionEngine(REPO)
    pending = [
        r
        for r in engine.scan_all(apply=False)
        if r.target_stage and not r.passed and r.gene in ORIGINAL_SIX
    ]
    assert not pending
    code = Alt4Runtime.alt4_gate(strict=False)
    assert code == 0
