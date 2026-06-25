"""Fitness heartbeat wiring — debt, risk, governance, amendments, missions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from constitutional.runtime import (
    ConstitutionalStateRuntime,
    FitnessGovernanceDecision,
    GovernanceGateDecision,
    ReconstructabilityDashboardState,
    ReconstructabilityFailureClass as RF,
    ReconstructabilityFitnessState,
    apply_dashboard_to_governance_gate,
    apply_fitness_to_debt,
    apply_fitness_to_governance_gate,
    apply_fitness_to_risk,
    compute_fitness_penalty,
    evaluate_fitness_governance_gate,
    load_constitutional_debt,
    load_dashboard_governance_decision,
    load_fitness_governance_decision,
    load_reconstructability_dashboard,
    load_reconstructability_risk,
    maybe_trigger_reconstructability_amendment,
)
from constitutional.runtime.amendment_triggers import (
    apply_dashboard_to_amendment_triggers,
    load_amendment_triggers,
)
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.personal_constitutional_state import PersonalConstitutionalStateRuntime
from constitutional.runtime.reconstructability_fitness_runtime import FITNESS_STATE_ID
from operator_kernel.heartbeat import (
    FITNESS_INTERVAL,
    constitutional_heartbeat,
    reset_fitness_schedule,
    run_dashboard_update,
    run_fitness_audit,
)
from operator_kernel.missions import can_launch_mission, can_launch_mission_with_dashboard
from operator_kernel.succession import maybe_initiate_succession, succession_ready


@pytest.fixture(autouse=True)
def _isolate_receipt_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    reset_fitness_schedule()


@pytest.fixture
def csr(tmp_path: Path) -> ConstitutionalStateRuntime:
    clear_domain_memory_index()
    return ConstitutionalStateRuntime(persist_root=tmp_path)


def _rf_state(
    *,
    fitness_score: float = 0.8,
    stewardship_readiness_score: float = 0.8,
    failed_surfaces: list[RF] | None = None,
    implicit_assumptions_required: int = 0,
) -> ReconstructabilityFitnessState:
    return ReconstructabilityFitnessState(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=1,
        fitness_score=fitness_score,
        stewardship_readiness_score=stewardship_readiness_score,
        failed_surfaces=failed_surfaces or [],
        implicit_assumptions_required=implicit_assumptions_required,
    )


def _dashboard(
    *,
    survivability: float = 0.8,
    steward: float = 0.8,
    founder_dependency: float = 0.2,
    fitness: float | None = None,
    threats: list[RF] | None = None,
) -> ReconstructabilityDashboardState:
    return ReconstructabilityDashboardState(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=1,
        system_survivability_score=survivability,
        steward_independence_score=steward,
        founder_dependency_index=founder_dependency,
        reconstructability_fitness_score=fitness if fitness is not None else survivability,
        constitutional_debt_score=0.1,
        constitutional_risk_score=0.1,
        personal_capacity_continuity=0.8,
        active_threats=threats or [],
    )


def test_compute_fitness_penalty() -> None:
    penalty = compute_fitness_penalty(
        failed_surfaces=[RF.EVIDENCE_LOSS, RF.LINEAGE_BREAK],
        implicit_assumptions_required=2,
    )
    assert penalty == pytest.approx(0.16)


def test_apply_fitness_to_debt_merges_threats(csr: ConstitutionalStateRuntime) -> None:
    rf_state = _rf_state(failed_surfaces=[RF.EVIDENCE_LOSS], implicit_assumptions_required=1)
    debt = apply_fitness_to_debt(csr, rf_state)
    assert debt.fitness_penalty == pytest.approx(0.08)
    assert RF.EVIDENCE_LOSS in debt.threats
    assert load_constitutional_debt(csr).debt_score == debt.debt_score


def test_apply_fitness_to_risk(csr: ConstitutionalStateRuntime) -> None:
    rf_state = _rf_state(fitness_score=0.3, stewardship_readiness_score=0.7)
    risk = apply_fitness_to_risk(csr, rf_state)
    assert risk.reconstructability_risk == pytest.approx(0.7)
    loaded = load_reconstructability_risk(csr)
    assert loaded is not None
    assert loaded.reconstructability_risk == risk.reconstructability_risk


def test_fitness_governance_gate_levels() -> None:
    ok = evaluate_fitness_governance_gate(_rf_state())
    assert ok.level == "ok" and ok.allow

    warn = evaluate_fitness_governance_gate(_rf_state(fitness_score=0.5, stewardship_readiness_score=0.8))
    assert warn.level == "warn" and warn.allow

    block = evaluate_fitness_governance_gate(_rf_state(fitness_score=0.2, stewardship_readiness_score=0.2))
    assert block.level == "block" and not block.allow


def test_apply_fitness_to_governance_gate_persists(csr: ConstitutionalStateRuntime) -> None:
    rf_state = _rf_state(fitness_score=0.2, stewardship_readiness_score=0.2)
    decision = apply_fitness_to_governance_gate(csr, rf_state)
    assert isinstance(decision, FitnessGovernanceDecision)
    loaded = load_fitness_governance_decision(csr)
    assert loaded is not None
    assert loaded.level == "block"


def test_amendment_triggers_on_persistent_failures(csr: ConstitutionalStateRuntime) -> None:
    rf_state = _rf_state(
        failed_surfaces=[RF.STEWARD_DISCONTINUITY, RF.EVIDENCE_LOSS, RF.LINEAGE_BREAK],
    )
    opened = maybe_trigger_reconstructability_amendment(csr, rf_state)
    assert len(opened) == 2
    pending = load_amendment_triggers(csr)
    scopes = {record.scope for record in pending.triggers}
    assert scopes == {"stewardship", "ledger_and_receipts"}


def test_pcs_increments_burnout_on_low_stewardship(csr: ConstitutionalStateRuntime) -> None:
    csr.put_domain_doc(
        FITNESS_STATE_ID,
        "reconstructability_fitness",
        _rf_state(stewardship_readiness_score=0.2),
    )
    pcs = PersonalConstitutionalStateRuntime(csr).update_snapshot()
    assert pcs.burnout_warnings >= 1


def test_can_launch_mission_gated_on_fitness(csr: ConstitutionalStateRuntime) -> None:
    assert can_launch_mission(object(), csr=csr) is False

    csr.put_domain_doc(
        FITNESS_STATE_ID,
        "reconstructability_fitness",
        _rf_state(fitness_score=0.7),
    )
    assert can_launch_mission(object(), csr=csr) is True

    csr.put_domain_doc(
        FITNESS_STATE_ID,
        "reconstructability_fitness",
        _rf_state(fitness_score=0.3),
    )
    assert can_launch_mission(object(), csr=csr) is False


def test_constitutional_heartbeat_runs_fitness_once_per_interval(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    first = constitutional_heartbeat(now, csr=csr, force_fitness=True)
    assert first is not None

    second = constitutional_heartbeat(now + timedelta(hours=1), csr=csr)
    assert second is None

    third = constitutional_heartbeat(now + FITNESS_INTERVAL, csr=csr)
    assert third is not None


def test_run_fitness_audit_end_to_end(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    state = run_fitness_audit(now, csr)
    assert isinstance(state, ReconstructabilityFitnessState)
    assert load_constitutional_debt(csr).fitness_penalty >= 0.0
    assert load_reconstructability_risk(csr) is not None
    assert load_fitness_governance_decision(csr) is not None
    dashboard = load_reconstructability_dashboard(csr)
    assert dashboard.version >= 1
    assert load_dashboard_governance_decision(csr) is not None


def test_dashboard_governance_gate_levels() -> None:
    ok = apply_dashboard_to_governance_gate(_dashboard())
    assert ok.level == "ok" and ok.allow
    assert ok.article_s1 is not None and ok.article_s1.compliant

    warn = apply_dashboard_to_governance_gate(_dashboard(survivability=0.65, founder_dependency=0.35))
    assert warn.level == "warn" and warn.allow

    block_survivability = apply_dashboard_to_governance_gate(_dashboard(survivability=0.55))
    assert block_survivability.level == "block" and not block_survivability.allow
    assert "0.60" in block_survivability.reason

    block_steward = apply_dashboard_to_governance_gate(_dashboard(steward=0.55))
    assert block_steward.level == "block" and not block_steward.allow

    block_founder = apply_dashboard_to_governance_gate(_dashboard(founder_dependency=0.45))
    assert block_founder.level == "block" and not block_founder.allow
    assert "Founder dependency" in block_founder.reason


def test_can_launch_mission_with_dashboard() -> None:
    assert can_launch_mission_with_dashboard(object(), _dashboard()) is True
    assert can_launch_mission_with_dashboard(object(), _dashboard(survivability=0.4)) is False
    assert can_launch_mission_with_dashboard(object(), _dashboard(founder_dependency=0.7)) is False


def test_succession_ready_threshold() -> None:
    fitness = ReconstructabilityFitnessState(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=1,
        fitness_score=0.8,
        stewardship_readiness_score=0.8,
    )
    assert succession_ready(_dashboard(survivability=0.8, steward=0.8, founder_dependency=0.2), fitness) is True
    assert succession_ready(_dashboard(survivability=0.6, steward=0.8), fitness) is False
    assert succession_ready(_dashboard(survivability=0.8, steward=0.8, founder_dependency=0.35), fitness) is False


def test_maybe_initiate_succession_opens_record(csr: ConstitutionalStateRuntime) -> None:
    fitness = ReconstructabilityFitnessState(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=1,
        fitness_score=0.8,
        stewardship_readiness_score=0.8,
    )
    dashboard = _dashboard(survivability=0.8, steward=0.8, founder_dependency=0.2, fitness=0.8)
    csr.put_domain_doc("reconstructability_dashboard__global", "reconstructability_dashboard", dashboard)
    record = maybe_initiate_succession(csr, dashboard, fitness=fitness)
    assert record is not None
    assert record.status == "open"


def test_dashboard_amendment_triggers(csr: ConstitutionalStateRuntime) -> None:
    collapse = _dashboard(survivability=0.35, threats=[RF.EVIDENCE_LOSS])
    opened_collapse = apply_dashboard_to_amendment_triggers(csr, collapse)
    collapse_scopes = {record.scope for record in opened_collapse}
    assert "survivability" in collapse_scopes
    assert "survivability_remediation" in collapse_scopes

    founder = _dashboard(
        founder_dependency=0.75,
        threats=[RF.STEWARD_DISCONTINUITY, RF.EVIDENCE_LOSS],
    )
    opened = apply_dashboard_to_amendment_triggers(csr, founder)
    pending = load_amendment_triggers(csr)
    scopes = {record.scope for record in pending.triggers}
    assert scopes >= {"stewardship", "ledger_and_receipts", "survivability_remediation"}


def test_run_dashboard_update_persists(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    csr.put_domain_doc(
        FITNESS_STATE_ID,
        "reconstructability_fitness",
        _rf_state(fitness_score=0.9, stewardship_readiness_score=0.85),
    )
    dashboard = run_dashboard_update(now, csr)
    assert isinstance(dashboard, ReconstructabilityDashboardState)
    assert dashboard.article_reference == "Article S — Survivability Doctrine"
    assert dashboard.governed_invariant == "CRITICAL_SYSTEMS_MUST_REMAIN_SURVIVABLE"
    loaded = load_reconstructability_dashboard(csr)
    assert loaded.version == dashboard.version
    decision = load_dashboard_governance_decision(csr)
    assert isinstance(decision, GovernanceGateDecision)
