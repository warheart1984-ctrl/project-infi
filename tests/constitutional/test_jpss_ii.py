"""Tests for JPSS-II — transferability law, dual validity, JPSS-C engine."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.core.articles import JPSS_II_MIN_TRANSFERABILITY_INDEX
from constitutional.eck2 import ECK2Runtime
from constitutional.jpss.constitutional_engine import (
    ConstitutionalGovernanceRequest,
    JPSSConstitutionalEngine,
    load_latest_constitutional_decision,
)
from constitutional.jpss.constitutional_register import load_constitutional_register
from constitutional.jpss.diagrams import JPSS_II_THREE_LAYER_STACK_DIAGRAM, format_jpss_diagrams
from constitutional.jpss.jpss_ii_spec import (
    JPSS_II_EVIDENCE_HIERARCHY,
    JPSS_II_TRANSFERABILITY_LAW,
    JPSS_II_VALIDITY_AXES,
    JPSS_RECURSIVE_CONDITION,
)
from constitutional.jpss.transferability import evaluate_jpss_transferability, load_transferability_report
from constitutional.jpss import canonical_passing_responses
from constitutional.legitimacy.jpss_c_exam import canonical_passing_constitutional_responses, run_jpss_c_exam
from constitutional.legitimacy.jpss_c_spec import JPSS_C_GOVERNANCE_CHAIN
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.runtime import ConstitutionalStateRuntime


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path) -> ConstitutionalStateRuntime:
    from constitutional.core.articles import PURPOSE_CONTINUITY_INVARIANT

    runtime = ConstitutionalStateRuntime(persist_root=tmp_path)
    runtime.register_invariant(PURPOSE_CONTINUITY_INVARIANT, "Article P")
    runtime.register_invariant(
        "CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE",
        "Article R",
    )
    return runtime


def _steward_inputs(**overrides):
    defaults = {
        "decision_id": "jpss-ii-dec-001",
        "steward_id": "independent-steward",
        "available_signals": ["fitness", "continuity"],
        "expected_signals": ["reconstructability"],
        "constraints_active": ["article_r"],
        "environmental_factors": ["succession_pressure"],
        "outcome": "observe",
        "rationale": "JPSS-II transferability stack.",
        "expected_result": "observe",
        "success": True,
        "invariant_defaults": {
            "purpose_clauses": ["preserve constitutional continuity"],
            "core_values": ["non-derogable", "reconstructable"],
            "commitments": ["succession gate required"],
            "identity_markers": ["eck-2 dual pipeline"],
            "sacred_constraints": ["never bypass succession gate"],
        },
        "stewardship_responses": canonical_passing_responses(),
    }
    defaults.update(overrides)
    return defaults


def _seed_transferability_stack(csr: ConstitutionalStateRuntime) -> None:
    ECK2Runtime(csr).run(_steward_inputs())
    run_jpss_c_exam(csr, "independent-steward", canonical_passing_constitutional_responses())
    JPSSConstitutionalEngine(csr).govern(
        ConstitutionalGovernanceRequest(
            action="invariant_elevation",
            target_layer="invariant",
            item="reconstructability",
            classification="boundary_consultation",
            rationale="Elevate reconstructability after independent cross-domain validation.",
            steward_id="independent-steward",
            reconstruction_evidence=["eck2_pipeline", "jpss_cycle"],
            consequence_simulation="Identity preserved; adaptive calibration remains flexible.",
            prior_classification="adaptive",
            new_classification="invariant",
        )
    )
    evaluate_jpss_transferability(csr)


def test_jpss_ii_spec_constants() -> None:
    assert len(JPSS_II_VALIDITY_AXES) == 2
    assert len(JPSS_II_EVIDENCE_HIERARCHY) == 6
    assert "transferable without its original stewards" in JPSS_II_TRANSFERABILITY_LAW
    assert JPSS_RECURSIVE_CONDITION == "JPSS itself is subject to JPSS."
    assert len(JPSS_C_GOVERNANCE_CHAIN) == 5


def test_three_layer_stack_diagram() -> None:
    assert "JPSS-A" in JPSS_II_THREE_LAYER_STACK_DIAGRAM
    assert "JPSS-C" in JPSS_II_THREE_LAYER_STACK_DIAGRAM
    assert "Boundary Governance" in JPSS_II_THREE_LAYER_STACK_DIAGRAM
    assert "Three-Layer Stack" in format_jpss_diagrams()


def test_constitutional_engine_blocks_without_evidence(csr: ConstitutionalStateRuntime) -> None:
    engine = JPSSConstitutionalEngine(csr)
    result = engine.govern(
        ConstitutionalGovernanceRequest(
            action="invariant_elevation",
            target_layer="invariant",
            item="core_value_x",
            classification="requires_legitimacy_review",
            rationale="Attempt elevation without evidence.",
        )
    )
    assert result.blocked
    assert "reconstruction evidence" in result.block_reason.lower()


def test_constitutional_engine_records_elevation(csr: ConstitutionalStateRuntime) -> None:
    result = JPSSConstitutionalEngine(csr).govern(
        ConstitutionalGovernanceRequest(
            action="invariant_elevation",
            target_layer="invariant",
            item="reconstructability",
            classification="boundary_consultation",
            rationale="Test elevation with evidence.",
            reconstruction_evidence=["jpss_cycle"],
            consequence_simulation="No identity collapse expected.",
        )
    )
    assert result.recorded
    register = load_constitutional_register(csr)
    assert len(register.entries) == 1
    assert load_latest_constitutional_decision(csr) is not None


def test_epistemic_validity_without_csr() -> None:
    from constitutional.jpss.transferability import _evaluate_epistemic_validity

    epistemic = _evaluate_epistemic_validity()
    assert epistemic.passed
    assert epistemic.score >= JPSS_II_MIN_TRANSFERABILITY_INDEX


def test_transferability_after_full_stack(csr: ConstitutionalStateRuntime) -> None:
    _seed_transferability_stack(csr)
    report = evaluate_jpss_transferability(csr)
    assert report.epistemic_validity.passed
    assert report.stewardship_validity.passed
    assert report.transferable
    assert report.continuity_marks["reconstructable"]
    assert report.continuity_marks["identity_preserving"]
    assert load_transferability_report(csr) is not None


def test_eck2_pipeline_includes_transferability(csr: ConstitutionalStateRuntime) -> None:
    _seed_transferability_stack(csr)
    from constitutional.eck2 import load_eck2_pipeline

    pipeline = load_eck2_pipeline(csr)
    assert pipeline is not None
    assert pipeline.transferability is not None
    assert pipeline.transferability.transferable
