"""Constitutional chain C1–C12, roots, oath, and temporal coherence proofs."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.continuity.constitutional_apply import (
    apply_constitutional_chain,
    load_fitness_history,
    run_c9_fitness_proof,
    run_c10_stewardship_proof,
    run_c11_interoperability_proof,
    run_c12_temporal_proof,
    run_kernel_enforcement_proof,
    run_root_00y_evolution_proof,
    run_root_00z_inheritance_proof,
)
from src.continuity.boot_ceremony import run_boot_ceremony_proof
from src.continuity.continuity_math import run_continuity_math_proof
from src.continuity.generative_law import run_git_1_proof
from src.continuity.genesis_lineage import run_genesis_lineage_proof
from src.continuity.invariant_engine import run_invariant_engine_proof
from src.continuity.nova_kernel_loop import run_genesis_kernel_loop_proof
from src.continuity.operator_kernel_interface import run_operator_kernel_interface_proof
from src.continuity.operator_training import run_ots_training_proof
from src.continuity.constitutional_chain import (
    CONSTITUTIONAL_CHAIN,
    OPERATORS_MANUAL_TEXT,
    OPERATORS_OATH_TEXT,
    ROOT_00X,
    ROOT_00Y,
    ROOT_00Z,
    UGR_C12_CANONICAL_TEXT,
    UGR_CONSTITUTION_ASSEMBLED_TEXT,
    UGR_PREAMBLE_TEXT,
    chain_index,
    validate_chain_dependencies,
)
from src.continuity.constitutional_kernel import ConstitutionalKernel, KernelViolation, NK_0001_CANONICAL_TEXT
from src.continuity.convergence_algebra import DEFAULT_DELTA_MAX, DEFAULT_PHI_MIN, convergence_fitness, fitness_within_tolerance
from src.continuity.creation_operator import CreationOperator, SubstrateState
from src.continuity.governed_evolution import DEFAULT_S_MIN, evaluate_stewardship
from src.continuity.inter_civilizational import Civilization, evaluate_interoperability
from src.continuity.lci_stack import lineages_from_fixture, load_lci_fixture
from src.continuity.meaning_ledger import MeaningLedger
from src.continuity.temporal_governance import TemporalState, evaluate_temporal_coherence, temporal_convergence_fitness


def test_constitutional_chain_order_and_dependencies() -> None:
    assert len(CONSTITUTIONAL_CHAIN) == 12
    assert CONSTITUTIONAL_CHAIN[-1].code == "UGR-C12"
    assert validate_chain_dependencies()["passed"] is True


def test_c12_temporal_coherence_for_lawful_evolution() -> None:
    lineages = lineages_from_fixture(load_lci_fixture())
    past = TemporalState("t1", lineages[0])
    state = SubstrateState(state_id="temporal-proof", lineage=lineages[0])
    extended = CreationOperator().create(
        state,
        add_events=frozenset({"evt-temporal-layer"}),
        generativity_delta=0.5,
    )
    future = TemporalState("t2", extended.lineage)
    result = evaluate_temporal_coherence(past, future)
    assert result["passed"] is True
    assert float(result["phi_t1_t2"]) >= 0.65


def test_operators_oath_and_assembled_constitution() -> None:
    assert "ROOT-00Z" in OPERATORS_OATH_TEXT
    assert "OM-0001" in OPERATORS_MANUAL_TEXT
    assert "NK-0001" in NK_0001_CANONICAL_TEXT
    assert "C12 — Inter-Temporal Governance" in UGR_CONSTITUTION_ASSEMBLED_TEXT
    assert "OM-0001" in UGR_CONSTITUTION_ASSEMBLED_TEXT
    assert "NK-0001" in UGR_CONSTITUTION_ASSEMBLED_TEXT
    index = chain_index()
    assert index["temporal_governance_law"] == "UGR-C12"
    assert index["chain_id"] == "ugr-continuity-spine-v7"
    assert index["operators_manual_version"] == "OM-0001"
    assert index["constitutional_kernel"] == "NK-0001"
    assert "operators_oath" in index
    assert "operators_manual" in index
    assert "ugr_constitution_assembled" in index


def test_apply_constitutional_chain_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    online = tmp_path / "online"
    online.mkdir()
    monkeypatch.setenv("AAIS_ONLINE_RUNTIME_DIR", str(online))
    monkeypatch.setenv("MEANING_LEDGER_PATH", str(online / "meaning-ledger.jsonl"))
    monkeypatch.setenv("CAB_STORE", str(online / "cab-ledger.jsonl"))
    monkeypatch.setenv("CONVERGENCE_FITNESS_HISTORY_PATH", str(online / "convergence-fitness-history.jsonl"))
    monkeypatch.setenv("LAW_LEDGER_PATH", str(online / "law-ledger.sqlite3"))
    monkeypatch.setenv("EVIDENCE_LEDGER_PATH", str(online / "evidence-ledger.sqlite3"))
    monkeypatch.setenv("COMPREHENSION_LEDGER_PATH", str(online / "comprehension-ledger.sqlite3"))
    monkeypatch.setenv("MIT_LEDGER_PATH", str(online / "mit-ledger.sqlite3"))

    first = apply_constitutional_chain()
    second = apply_constitutional_chain()

    assert first["stack_ready"] is True
    assert first["chain_entries_added"] == 32
    assert second["chain_entries_added"] == 0
    assert first["c12_temporal_coherence"]["passed"] is True
    assert first["nk_kernel_enforcement"]["passed"] is True
    assert first["genesis_kernel_loop"]["passed"] is True
    assert first["comprehension_invariance_cit_1"]["passed"] is True
    assert first["meaning_invariance_mit_1"]["passed"] is True
    assert first["evidence_convergence_eit_2"]["passed"] is True

    ledger = MeaningLedger()
    assert ledger.get("ML-UGR-CHAIN-003") is not None
    assert ledger.get("ML-UGR-C12-CANONICAL-001") is not None
    assert ledger.get("ML-UGR-OPERATORS-OATH-001") is not None
    assert ledger.get("ML-UGR-OPERATORS-MANUAL-001") is not None
    assert ledger.get("ML-NK-CONSTITUTIONAL-KERNEL-001") is not None
    assert ledger.get("ML-CM-CONTINUITY-MATH-001") is not None
    assert ledger.get("ML-IE-INVARIANT-ENGINE-001") is not None
    assert ledger.get("ML-OKI-OPERATOR-KERNEL-001") is not None
    assert ledger.get("ML-UGR-GIT-1-001") is not None
    assert ledger.get("ML-LAW-LEDGER-001") is not None
    assert ledger.get("ML-UGR-EIT-1-001") is not None
    assert ledger.get("ML-UGR-CIT-1-001") is not None
    assert ledger.get("ML-UGR-MIT-1-001") is not None
    assert ledger.get("ML-UGR-EIT-2-001") is not None
    assert ledger.get("ML-UGR-CONSTITUTION-001") is not None
    assert ROOT_00Z in ledger.get("ML-UGR-OPERATORS-OATH-001").lineage

    assert len(load_fitness_history()) >= 1


def test_run_all_proofs() -> None:
    assert run_c9_fitness_proof()["passed"] is True
    assert run_c10_stewardship_proof()["passed"] is True
    assert run_root_00y_evolution_proof()["passed"] is True
    assert run_root_00z_inheritance_proof()["passed"] is True
    assert run_c11_interoperability_proof()["passed"] is True
    assert run_c12_temporal_proof()["passed"] is True
    assert run_kernel_enforcement_proof()["passed"] is True
    assert run_ots_training_proof()["passed"] is True
    assert run_genesis_lineage_proof()["passed"] is True
    assert run_boot_ceremony_proof()["passed"] is True
    assert run_continuity_math_proof()["passed"] is True
    assert run_invariant_engine_proof()["passed"] is True
    assert run_operator_kernel_interface_proof()["passed"] is True
    assert run_git_1_proof()["passed"] is True
    assert run_genesis_kernel_loop_proof()["passed"] is True


def test_kernel_rejects_continuity_annihilation() -> None:
    lineages = lineages_from_fixture(load_lci_fixture())
    before = SubstrateState("s", lineages[0])
    shrunk = replace(lineages[0], event_ids=frozenset({"evt-only-new"}))
    after = SubstrateState("s-prime", shrunk)
    kernel = ConstitutionalKernel()
    with pytest.raises(KernelViolation):
        kernel.evolve(before, after, lineages)


def test_c11_interoperability_bridge_fixture() -> None:
    lineages = lineages_from_fixture(load_lci_fixture())
    alpha, beta, gamma = lineages[0], lineages[1], lineages[2]
    shared_bridge = replace(
        alpha,
        lineage_id="L-shared-bridge",
        event_ids=alpha.event_ids | frozenset({"evt-converge-seed", "evt-nexus-handoff"}),
        generativity=max(alpha.generativity, beta.generativity),
    )
    result = evaluate_interoperability(
        Civilization("a", (alpha, beta)),
        Civilization("b", (shared_bridge, gamma)),
    )
    assert result["passed"] is True


def test_temporal_fitness_monotonic_under_extension() -> None:
    lineages = lineages_from_fixture(load_lci_fixture())
    past = TemporalState("t1", lineages[0])
    extended = CreationOperator().create(
        SubstrateState("s", lineages[0]),
        add_events=frozenset({"evt-future"}),
        generativity_delta=1.0,
    ).lineage
    future = TemporalState("t2", extended)
    divergent = TemporalState("t2-divergent", lineages[1])

    fitness = temporal_convergence_fitness(past, future)
    divergent_fitness = temporal_convergence_fitness(past, divergent)

    assert fitness >= DEFAULT_PHI_MIN
    assert fitness > divergent_fitness
