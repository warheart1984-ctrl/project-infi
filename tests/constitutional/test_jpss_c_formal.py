"""Tests for JPSS-C formal specification — cycle, engines, drift, transferability test."""

from __future__ import annotations

import pytest

from constitutional.eck2 import ECK2Runtime
from constitutional.jpss.constitutional_drift import detect_constitutional_drift
from constitutional.jpss.constitutional_engine import (
    ConstitutionalGovernanceRequest,
    JPSSConstitutionalEngine,
)
from constitutional.jpss.constitutional_ledgers import (
    load_elevation_review_ledger,
    load_invariant_candidate_ledger,
    load_retirement_review_ledger,
)
from constitutional.jpss.invariant_retirement_protocol import (
    InvariantRetirementProtocol,
    InvariantRetirementRequest,
)
from constitutional.jpss.invariant_selection_engine import (
    InvariantSelectionEngine,
    InvariantSelectionRequest,
)
from constitutional.jpss.transferability_test import run_jpss_transferability_test
from constitutional.jpss import canonical_passing_responses
from constitutional.legitimacy.jpss_c_exam import canonical_passing_constitutional_responses, run_jpss_c_exam
from constitutional.legitimacy.jpss_c_spec import (
    JPSS_C_CANONICAL_CYCLE,
    JPSS_C_CANONICAL_QUESTIONS,
    JPSS_C_DAR_Z_QA,
    JPSS_C_DRIFT_MODES,
    JPSS_C_ELEVATION_CRITERIA,
    JPSS_C_REGISTER_NAMES,
    JPSS_C_RETIREMENT_CRITERIA,
    JPSS_C_RETIREMENT_STEPS,
    JPSS_C_SELECTION_DIMENSIONS,
    JPSS_C_TRANSFERABILITY_TEST_COMPONENTS,
)
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
        "decision_id": "jpss-c-dec-001",
        "steward_id": "independent-steward",
        "available_signals": ["fitness", "continuity"],
        "expected_signals": ["reconstructability"],
        "constraints_active": ["article_r"],
        "environmental_factors": ["succession_pressure"],
        "outcome": "observe",
        "rationale": "JPSS-C formal stack.",
        "expected_result": "observe",
        "success": True,
        "invariant_defaults": {
            "purpose_clauses": ["preserve constitutional continuity"],
            "core_values": ["non-derogable", "reconstructable", "obsolete_value"],
            "commitments": ["succession gate required"],
            "identity_markers": ["eck-2 dual pipeline"],
            "sacred_constraints": ["never bypass succession gate"],
        },
        "stewardship_responses": canonical_passing_responses(),
    }
    defaults.update(overrides)
    return defaults


def test_jpss_c_formal_spec_constants() -> None:
    assert len(JPSS_C_CANONICAL_CYCLE) == 8
    assert len(JPSS_C_CANONICAL_QUESTIONS) == 6
    assert len(JPSS_C_ELEVATION_CRITERIA) == 6
    assert len(JPSS_C_RETIREMENT_CRITERIA) == 6
    assert len(JPSS_C_REGISTER_NAMES) == 4
    assert len(JPSS_C_DRIFT_MODES) == 4
    assert len(JPSS_C_SELECTION_DIMENSIONS) == 7
    assert len(JPSS_C_RETIREMENT_STEPS) == 8
    assert len(JPSS_C_TRANSFERABILITY_TEST_COMPONENTS) == 5
    assert len(JPSS_C_DAR_Z_QA) == 20


def test_invariant_selection_engine_elevates(csr: ConstitutionalStateRuntime) -> None:
    ECK2Runtime(csr).run(_steward_inputs())
    result = InvariantSelectionEngine(csr).evaluate(
        InvariantSelectionRequest(
            candidate_value="reconstructability",
            protects_purpose=True,
            prevents_catastrophic_drift=True,
            defines_identity=True,
            required_for_reconstructability=True,
            stabilizes_long_term_coherence=True,
            purpose_clauses=["preserve constitutional continuity"],
            identity_markers=["eck-2 dual pipeline"],
        )
    )
    assert result.outcome == "elevate_to_invariant"
    assert len(result.criteria_met) >= 3
    assert len(load_invariant_candidate_ledger(csr).entries) == 1
    assert len(load_elevation_review_ledger(csr).entries) == 1


def test_invariant_selection_engine_rejects_weak_candidate(csr: ConstitutionalStateRuntime) -> None:
    result = InvariantSelectionEngine(csr).evaluate(
        InvariantSelectionRequest(candidate_value="ephemeral_preference")
    )
    assert result.outcome in ("reject", "keep_adaptive", "escalate_to_constitutional_review")


def test_invariant_retirement_protocol(csr: ConstitutionalStateRuntime) -> None:
    ECK2Runtime(csr).run(_steward_inputs())
    result = InvariantRetirementProtocol(csr).execute(
        InvariantRetirementRequest(
            invariant_item="obsolete_value",
            invariant_field="core_values",
            purpose_no_longer_applies=True,
            historically_contingent=True,
            steward_consensus=True,
            drift_triggered=True,
            context_reconstruction="Historical context reconstructed.",
            purpose_reevaluation="Purpose no longer requires this value.",
            identity_impact="No identity collapse expected.",
            failure_risk_model="Low failure risk after retirement.",
            deliberation_notes="Stewards agree on retirement.",
            retirement_vote_approved=True,
        )
    )
    assert result.retirement_approved
    assert result.register_updated
    assert len(load_retirement_review_ledger(csr).entries) == 1


def test_constitutional_drift_detector(csr: ConstitutionalStateRuntime) -> None:
    ECK2Runtime(csr).run(_steward_inputs())
    report = detect_constitutional_drift(csr)
    assert "boundary_stability" in report.component_scores
    assert len(report.drift_types) == 6
    assert report.drift_index >= 0.0


def test_transferability_test_five_components(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.jpss.transferability import evaluate_jpss_transferability

    ECK2Runtime(csr).run(_steward_inputs())
    run_jpss_c_exam(csr, "independent-steward", canonical_passing_constitutional_responses())
    JPSSConstitutionalEngine(csr).govern(
        ConstitutionalGovernanceRequest(
            action="invariant_elevation",
            target_layer="invariant",
            item="reconstructability",
            classification="boundary_consultation",
            rationale="Elevation after formal validation.",
            steward_id="independent-steward",
            reconstruction_evidence=["eck2_pipeline"],
            consequence_simulation="Identity preserved.",
        )
    )
    evaluate_jpss_transferability(csr)
    test_report = run_jpss_transferability_test(csr)
    assert len(test_report.components) == 5
    assert test_report.passed
