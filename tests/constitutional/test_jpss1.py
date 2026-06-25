"""Tests for JPSS-1 judgment formation pipeline."""

from __future__ import annotations

import pytest

from constitutional.jpss import (
    JPSS_CANONICAL_CYCLE,
    JPSS_DRIFT_CLASSES,
    JPSSFormationRuntime,
    detect_jpss_drift,
    load_decision_register,
    load_jpss_cycle,
    load_perception_register,
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
        "decision_id": "jpss-dec-001",
        "available_signals": ["fitness", "continuity"],
        "expected_signals": ["reconstructability"],
        "constraints_active": ["article_r"],
        "environmental_factors": ["succession_pressure"],
        "outcome": "observe",
        "rationale": "Judgment cycle preservation audit.",
        "expected_result": "observe",
        "success": True,
    }
    defaults.update(overrides)
    return defaults


def test_jpss_canonical_cycle_has_eight_stages() -> None:
    assert len(JPSS_CANONICAL_CYCLE) == 8
    assert JPSS_CANONICAL_CYCLE[0] == "environment"
    assert JPSS_CANONICAL_CYCLE[-1] == "calibration_update"


def test_jpss_formation_runtime_completes_cycle(csr: ConstitutionalStateRuntime) -> None:
    runtime = JPSSFormationRuntime(csr)
    cycle = runtime.run(_steward_inputs())
    assert cycle.decision_id == "jpss-dec-001"
    assert cycle.stages_completed == list(JPSS_CANONICAL_CYCLE)
    assert cycle.environment.constraints_active
    assert cycle.perception.available_signals
    assert cycle.salience.primary_signals
    assert cycle.decision.outcome == "observe"
    assert cycle.outcome.success is True
    assert cycle.reflection.lessons
    assert cycle.calibration_update.decision_id == "jpss-dec-001"


def test_jpss_registers_persist(csr: ConstitutionalStateRuntime) -> None:
    JPSSFormationRuntime(csr).run(_steward_inputs())
    perception = load_perception_register(csr)
    decision = load_decision_register(csr)
    assert perception.latest_for_decision("jpss-dec-001") is not None
    assert decision.latest_for_decision("jpss-dec-001") is not None
    assert load_jpss_cycle(csr) is not None


def test_jpss_drift_detectable_after_formation(csr: ConstitutionalStateRuntime) -> None:
    cycle = JPSSFormationRuntime(csr).run(_steward_inputs())
    report = detect_jpss_drift(csr, decision_id=cycle.decision_id, cycle=cycle)
    assert report.drift_detectable
    assert len(report.findings) == len(JPSS_DRIFT_CLASSES)
    assert not report.active_drifts
