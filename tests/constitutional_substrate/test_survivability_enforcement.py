"""Article S-1 survivability enforcement tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from constitutional.core.articles import (
    FOUNDER_DEPENDENCY_CONSTITUTIONAL_MAX,
    STEWARD_INDEPENDENCE_CONSTITUTIONAL_MIN,
    SURVIVABILITY_CONSTITUTIONAL_MIN,
)
from constitutional.runtime import ConstitutionalStateRuntime, ReconstructabilityDashboardState
from constitutional.runtime.survivability_enforcement import (
    COLD_START_TEST_INTERVAL,
    SurvivabilityZone,
    build_succession_readiness_checklist,
    classify_dashboard_metrics,
    cold_start_test_due,
    compute_succession_readiness_score,
    evaluate_article_s1_compliance,
    load_cold_start_schedule,
    record_cold_start_run,
)
from operator_kernel.heartbeat import FITNESS_INTERVAL, reset_fitness_schedule


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    reset_fitness_schedule()


@pytest.fixture
def csr(tmp_path: Path) -> ConstitutionalStateRuntime:
    return ConstitutionalStateRuntime(persist_root=tmp_path)


def _dashboard(
    *,
    survivability: float = 0.8,
    steward: float = 0.8,
    founder_dependency: float = 0.2,
    fitness: float = 0.8,
    implicit: int = 0,
) -> ReconstructabilityDashboardState:
    return ReconstructabilityDashboardState(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=1,
        system_survivability_score=survivability,
        steward_independence_score=steward,
        founder_dependency_index=founder_dependency,
        reconstructability_fitness_score=fitness,
        constitutional_debt_score=0.1,
        constitutional_risk_score=0.1,
        personal_capacity_continuity=0.8,
        implicit_assumptions_required=implicit,
    )


def test_article_s1_constitutional_threshold_constants() -> None:
    assert SURVIVABILITY_CONSTITUTIONAL_MIN == 0.60
    assert STEWARD_INDEPENDENCE_CONSTITUTIONAL_MIN == 0.60
    assert FOUNDER_DEPENDENCY_CONSTITUTIONAL_MAX == 0.40


def test_survivability_zone_classification() -> None:
    green = classify_dashboard_metrics(_dashboard())
    assert green["system_survivability_score"] == SurvivabilityZone.GREEN
    assert green["founder_dependency_index"] == SurvivabilityZone.GREEN

    yellow = classify_dashboard_metrics(_dashboard(survivability=0.65, founder_dependency=0.35))
    assert yellow["system_survivability_score"] == SurvivabilityZone.YELLOW
    assert yellow["founder_dependency_index"] == SurvivabilityZone.YELLOW

    red = classify_dashboard_metrics(_dashboard(survivability=0.55, founder_dependency=0.45))
    assert red["system_survivability_score"] == SurvivabilityZone.RED
    assert red["founder_dependency_index"] == SurvivabilityZone.RED


def test_evaluate_article_s1_compliance_breach() -> None:
    compliance = evaluate_article_s1_compliance(_dashboard(survivability=0.55, steward=0.55))
    assert not compliance.compliant
    assert compliance.constitutional_breach
    assert "system_survivability_below_0.60" in compliance.breach_reasons


def test_succession_readiness_checklist_and_score() -> None:
    dashboard = _dashboard()
    checklist = build_succession_readiness_checklist(dashboard)
    assert checklist.all_pass
    score = compute_succession_readiness_score(dashboard)
    assert score >= 0.70


def test_cold_start_weekly_schedule(csr: ConstitutionalStateRuntime) -> None:
    dashboard = _dashboard()
    schedule = load_cold_start_schedule(csr)
    due, reason = cold_start_test_due(schedule, dashboard)
    assert due is True
    assert reason == "initial"

    record_cold_start_run(csr, dashboard, reason="initial")
    schedule = load_cold_start_schedule(csr)
    due_later, _ = cold_start_test_due(
        schedule,
        dashboard,
        now=dashboard.snapshot_at + timedelta(hours=1),
    )
    assert due_later is False

    due_week, reason_week = cold_start_test_due(
        schedule,
        dashboard,
        now=dashboard.snapshot_at + COLD_START_TEST_INTERVAL,
    )
    assert due_week is True
    assert reason_week == "weekly"


def test_fitness_interval_is_six_hours() -> None:
    assert FITNESS_INTERVAL == timedelta(hours=6)
