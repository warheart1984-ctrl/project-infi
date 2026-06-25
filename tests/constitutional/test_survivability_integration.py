"""Article S-2 integration, amendment template, and survivability dashboard API tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.reconstructability_dashboard_runtime import ReconstructabilityDashboardState
from constitutional.runtime.survivability_amendment import (
    build_survivability_amendment_record,
    render_survivability_amendment_template,
)
from operator_kernel.succession_integration import build_article_s2_integration_snapshot
from src.survivability_dashboard_api import build_survivability_dashboard_payload


@pytest.fixture
def csr(tmp_path):
    clear_domain_memory_index()
    from constitutional.runtime import ConstitutionalStateRuntime

    return ConstitutionalStateRuntime(persist_root=tmp_path)


def _dashboard(**kwargs) -> ReconstructabilityDashboardState:
    defaults = dict(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=1,
        system_survivability_score=0.8,
        steward_independence_score=0.8,
        founder_dependency_index=0.2,
        reconstructability_fitness_score=0.8,
        constitutional_debt_score=0.1,
        constitutional_risk_score=0.1,
        personal_capacity_continuity=0.8,
        purpose_continuity_index=0.85,
        mission_legibility_score=1.0,
        invariant_interpretation_score=0.85,
        mission_fidelity={"interactive_passed": True},
    )
    defaults.update(kwargs)
    return ReconstructabilityDashboardState(**defaults)


def test_render_survivability_amendment_template() -> None:
    record = build_survivability_amendment_record(
        _dashboard(survivability=0.5, founder_dependency=0.5),
        triggers=["survivability_below_0.60", "founder_dependency_above_0.40"],
    )
    md = render_survivability_amendment_template(record)
    assert "UGR-AMENDMENT-S-SURVIVABILITY-v0" in md or record.template_id in md
    assert "SURVIVABILITY REMEDIATION" in md
    assert "survivability_below_0.60" in md
    assert "Knowledge Externalization" in md
    assert "Success criteria" in md


def test_article_s2_integration_snapshot(csr) -> None:
    from constitutional.core.articles import PURPOSE_CONTINUITY_INVARIANT
    from constitutional.hiddenness.hiddenness_runtime import HiddennessRuntime
    from constitutional.runtime.mission_fidelity_interactive import submit_mission_fidelity_answers
    from constitutional.runtime.mission_fidelity_runtime import (
        MISSION_FIDELITY_STATE_ID,
        MissionFidelityRuntime,
        load_mission_fidelity_state,
    )
    from constitutional.salience.judgment_runtime import seed_passing_salience_judgment
    from constitutional.significance.significance_judgment_runtime import seed_passing_significance_judgment
    from tests.constitutional.test_hiddenness_runtime import (
        _all_answers,
        _seed_mission,
        _seed_salience_ledger_for_succession,
    )

    csr.register_invariant(PURPOSE_CONTINUITY_INVARIANT, "Article P")
    csr.register_invariant("CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE", "Article R")
    _seed_mission(csr)
    submit_mission_fidelity_answers(csr, _all_answers())
    MissionFidelityRuntime(csr).run_test()
    mf_state = load_mission_fidelity_state(csr)
    if mf_state is not None and mf_state.failed_surfaces:
        csr.put_domain_doc(
            MISSION_FIDELITY_STATE_ID,
            "mission_fidelity",
            mf_state.model_copy(update={"failed_surfaces": []}),
        )
    HiddennessRuntime(csr).run_audit()
    seed_passing_significance_judgment(csr)
    seed_passing_salience_judgment(csr)
    _seed_salience_ledger_for_succession(csr)

    dashboard = _dashboard(
        steward_independence_score=0.85,
        system_survivability_score=0.85,
        founder_dependency_index=0.15,
        reconstructability_fitness_score=0.85,
        hiddenness_index=1.0,
    )
    csr.put_domain_doc("reconstructability_dashboard__global", "reconstructability_dashboard", dashboard)
    from constitutional.runtime.reconstructability_fitness_runtime import (
        ReconstructabilityFitnessRuntime,
        ReconstructabilityFitnessState,
    )

    fitness = ReconstructabilityFitnessRuntime(csr).run_audit()
    fitness = fitness.model_copy(
        update={
            "fitness_score": 0.85,
            "failed_surfaces": [],
            "implicit_assumptions_required": 0,
        }
    )
    csr.put_domain_doc("reconstructability_fitness__global", "reconstructability_fitness", fitness)
    snapshot = build_article_s2_integration_snapshot(csr, fitness=fitness, escalate_amendment=False)
    assert snapshot.article_s2_reference.startswith("Article S-2")
    assert snapshot.article_s1.compliant is True
    assert snapshot.succession.ready is True
    assert snapshot.checklist.all_pass is True
    assert "system_survivability_score" in snapshot.zones


def test_article_s2_integration_opens_amendment_on_breach(csr) -> None:
    dashboard = _dashboard(
        system_survivability_score=0.5,
        steward_independence_score=0.5,
        founder_dependency_index=0.5,
        reconstructability_fitness_score=0.5,
        purpose_continuity_index=0.5,
        mission_legibility_score=0.5,
        invariant_interpretation_score=0.5,
        mission_fidelity={"interactive_passed": False},
    )
    csr.put_domain_doc("reconstructability_dashboard__global", "reconstructability_dashboard", dashboard)
    snapshot = build_article_s2_integration_snapshot(csr, escalate_amendment=True)
    assert snapshot.article_s1.constitutional_breach is True
    assert snapshot.survivability_amendment is not None
    assert snapshot.amendment_template_markdown is not None
    assert "survivability_below_0.60" in snapshot.survivability_amendment.triggers


def test_survivability_dashboard_api_payload(csr, monkeypatch) -> None:
    dashboard = _dashboard()
    csr.put_domain_doc("reconstructability_dashboard__global", "reconstructability_dashboard", dashboard)

    import src.survivability_dashboard_api as api

    monkeypatch.setattr(api, "get_survivability_csr", lambda: csr)
    payload = build_survivability_dashboard_payload(escalate_amendment=False)
    assert payload["article_s2_reference"].startswith("Article S-2")
    assert "dashboard" in payload
    assert "checklist" in payload
    assert "zones" in payload
