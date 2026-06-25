"""Tests for JPSS diagrams, drift taxonomy, and steward competency model."""

from __future__ import annotations

import pytest

from constitutional.eck2.compliance import evaluate_eck2_compliance
from constitutional.eck2.spec import ECK2_RECONSTRUCTION_PIPELINE
from constitutional.jpss.competency import (
    STEWARD_COMPETENCY_DOMAINS,
    assess_steward_competency,
    format_competency_model,
)
from constitutional.jpss.diagrams import (
    JPSS_DUAL_PIPELINE_DIAGRAM,
    JPSS_FORMATION_LOOP_DIAGRAM,
    format_jpss_diagrams,
)
from constitutional.jpss.drift_taxonomy import (
    JPSS_DRIFT_SUBTYPES,
    build_drift_taxonomy_report,
    format_drift_taxonomy,
    list_drift_taxonomy,
)
from constitutional.jpss import JPSSFormationRuntime
from constitutional.eck2 import ECK2Runtime
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


def _inputs(**overrides):
    defaults = {
        "decision_id": "spec-dec-001",
        "available_signals": ["fitness"],
        "constraints_active": ["article_r"],
        "outcome": "observe",
        "rationale": "Spec encoding test.",
        "expected_result": "observe",
        "success": True,
    }
    defaults.update(overrides)
    return defaults


def test_jpss_diagrams_contain_canonical_stages() -> None:
    assert "Environment" in JPSS_FORMATION_LOOP_DIAGRAM
    assert "Calibration Update" in JPSS_FORMATION_LOOP_DIAGRAM
    assert "FORMATION (JPSS-F" in JPSS_DUAL_PIPELINE_DIAGRAM
    assert "RECONSTRUCTION (ECK-R" in JPSS_DUAL_PIPELINE_DIAGRAM
    assert "UGR" in format_jpss_diagrams()


def test_drift_taxonomy_has_28_subtypes() -> None:
    assert len(JPSS_DRIFT_SUBTYPES) == 28
    assert len(list_drift_taxonomy()) == 28
    assert "E-D1" in format_drift_taxonomy()
    assert "PR-D5" in format_drift_taxonomy()


def test_drift_taxonomy_report_after_formation(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.jpss.drift import detect_jpss_drift

    cycle = JPSSFormationRuntime(csr).run(_inputs())
    layer = detect_jpss_drift(csr, decision_id=cycle.decision_id, cycle=cycle)
    report = build_drift_taxonomy_report(layer)
    assert len(report.subtype_findings) == 28
    assert not report.active_subtypes


def test_steward_competency_model_domains() -> None:
    assert len(STEWARD_COMPETENCY_DOMAINS) == 8
    assert "reconstruction" in STEWARD_COMPETENCY_DOMAINS
    assert "Environment" in format_competency_model()


def test_steward_competency_passes_after_dual_pipeline(csr: ConstitutionalStateRuntime) -> None:
    ECK2Runtime(csr).run(_inputs())
    assessment = assess_steward_competency(csr)
    assert assessment.dual_pipeline_demonstrated
    assert assessment.overall_score >= 0.75
    assert assessment.passed


def test_eck2_reconstruction_pipeline_matches_spec() -> None:
    assert ECK2_RECONSTRUCTION_PIPELINE[-1] == "continuity_update"
    assert ECK2_RECONSTRUCTION_PIPELINE[-2] == "significance_reconstruction"


def test_eck2_compliance_after_pipeline(csr: ConstitutionalStateRuntime) -> None:
    ECK2Runtime(csr).run(_inputs())
    report = evaluate_eck2_compliance(csr)
    assert report.compliant
    assert len(report.items) == 4
