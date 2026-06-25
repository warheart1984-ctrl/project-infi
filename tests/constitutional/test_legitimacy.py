"""Tests for Stewardship Legitimacy Protocol v1.0 — authority by reconstruction."""

from __future__ import annotations

import pytest

from constitutional.core.articles import ARTICLE_LEGITIMACY_ID, MIN_LEGITIMACY_INDEX
from constitutional.legitimacy import (
    JUDGMENT_STACK_LAYERS,
    LEGITIMACY_CRITERIA,
    LEGITIMACY_CRITERION_DEMONSTRATIONS,
    LEGITIMACY_DRIFT_CLASSES,
    LEGITIMACY_PROCESS_PHASES,
    LEGITIMACY_RECEIPT_TYPES,
    evaluate_reconstruction_demonstration,
    format_stewardship_legitimacy_protocol_v1,
    may_alter_invariant_layer,
    passing_reconstruction_demonstration,
    run_jpss_c_exam,
)
from constitutional.legitimacy.jpss_c_exam import canonical_passing_constitutional_responses
from constitutional.legitimacy.legitimacy_drift import LegitimacyDriftFailure, detect_legitimacy_drift
from constitutional.legitimacy.legitimacy_gate import check_steward_certification
from constitutional.legitimacy.legitimacy_process import load_legitimacy_process_result
from constitutional.legitimacy.legitimacy_receipts import load_legitimacy_receipts
from constitutional.legitimacy.seed import seed_stewardship_legitimacy
from constitutional.legitimacy.spec import LEGITIMACY_CRITERION_RULE, LEGITIMACY_STABILITY_REQUIREMENTS
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


def test_four_layer_judgment_stack() -> None:
    assert len(JUDGMENT_STACK_LAYERS) == 4
    assert JUDGMENT_STACK_LAYERS[-1] == "legitimacy"


def test_protocol_v1_spec_shape() -> None:
    assert len(LEGITIMACY_CRITERIA) == 6
    assert len(LEGITIMACY_CRITERION_DEMONSTRATIONS) == 6
    assert len(LEGITIMACY_PROCESS_PHASES) == 5
    assert len(LEGITIMACY_DRIFT_CLASSES) == 7
    assert len(LEGITIMACY_RECEIPT_TYPES) == 5
    assert len(LEGITIMACY_STABILITY_REQUIREMENTS) == 8
    text = format_stewardship_legitimacy_protocol_v1()
    assert "Stewardship Legitimacy Protocol v1.0" in text
    assert "drift_detection_competence" in text or "Drift Detection" in text


def test_reconstruction_criterion_all_demonstrations() -> None:
    demo = passing_reconstruction_demonstration("steward-a")
    result = evaluate_reconstruction_demonstration(demo)
    assert result.passed
    assert result.legitimacy_index == 1.0
    assert len(result.demonstrations_met) == 6
    assert "drift_detection_competence" in result.demonstrations_met
    assert LEGITIMACY_CRITERION_RULE.startswith("No one is legitimate")


def test_jpss_c_exam_passes_canonical_responses(csr: ConstitutionalStateRuntime) -> None:
    result = run_jpss_c_exam(csr, "steward-a", canonical_passing_constitutional_responses())
    assert result.passed
    assert result.scenarios_passed == result.scenarios_total


def test_may_alter_invariant_blocked_without_certification(csr: ConstitutionalStateRuntime) -> None:
    ok, message = may_alter_invariant_layer(csr, "steward-a")
    assert ok is False
    assert "certified" in message.lower() or "legitimacy" in message.lower()


def test_may_alter_invariant_with_plurality(csr: ConstitutionalStateRuntime) -> None:
    seed_stewardship_legitimacy(csr)
    ok, message = may_alter_invariant_layer(csr, "steward-a")
    assert ok is True
    assert "authorized" in message.lower()


def test_legitimacy_process_and_receipts_after_seed(csr: ConstitutionalStateRuntime) -> None:
    seed_stewardship_legitimacy(csr)
    process = load_legitimacy_process_result(csr, "steward-a")
    assert process is not None
    assert process.passed
    assert len(process.phases) == 5
    receipts = load_legitimacy_receipts(csr, "steward-a")
    assert receipts is not None
    assert receipts.complete


def test_legitimacy_drift_detects_single_steward_plurality_gap(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.legitimacy.legitimacy_register import certify_steward

    certify_steward(
        csr,
        steward_id="solo-steward",
        certified_by=["founder"],
        exam_passed=True,
        process_passed=False,
        legitimacy_index=0.95,
        receipt_refs=[],
    )
    drift = detect_legitimacy_drift(csr)
    assert LegitimacyDriftFailure.OVER_CONCENTRATION in drift.failed_surfaces
    assert drift.over_concentration_signals


def test_check_steward_certification(csr: ConstitutionalStateRuntime) -> None:
    seed_stewardship_legitimacy(csr)
    ok, _ = check_steward_certification(csr, "steward-a")
    assert ok is True


def test_article_legitimacy_registered() -> None:
    from constitutional import constitutional_registry

    article = constitutional_registry.get_article(ARTICLE_LEGITIMACY_ID)
    assert article is not None
    assert article["non_derogable"] is True
