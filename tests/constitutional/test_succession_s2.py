"""Article S-2 succession protocol and survivability amendment tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional import ARTICLE_S2, constitutional_registry
from constitutional.core.articles import (
    FOUNDER_DEPENDENCY_MANDATORY_SUCCESSION_THRESHOLD,
    MANDATORY_SUCCESSION_CYCLES,
    SUCCESSION_MAX_FOUNDER_DEPENDENCY,
    PURPOSE_CONTINUITY_INVARIANT,
)
from constitutional.runtime import ConstitutionalStateRuntime
from constitutional.runtime.amendment_triggers import apply_dashboard_to_amendment_triggers
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.reconstructability_dashboard_runtime import ReconstructabilityDashboardState
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessState
from constitutional.runtime.survivability_amendment import (
    evaluate_survivability_amendment_triggers,
    load_survivability_amendment,
    open_or_escalate_survivability_amendment,
)
from operator_kernel.succession import (
    apply_mandatory_succession_obligations,
    evaluate_succession_preconditions,
    load_succession_mandatory_tracker,
    maybe_initiate_succession,
    succession_blocked,
    succession_ready,
    track_mandatory_succession_cycle,
)


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path) -> ConstitutionalStateRuntime:
    runtime = ConstitutionalStateRuntime(persist_root=tmp_path)
    runtime.register_invariant(PURPOSE_CONTINUITY_INVARIANT, "Article P")
    runtime.register_invariant(
        "CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE",
        "Article R",
    )
    return runtime


def _dashboard(
    *,
    survivability: float = 0.8,
    steward: float = 0.8,
    founder_dependency: float | None = None,
    fitness: float | None = None,
    version: int = 1,
    threats: list[RF] | None = None,
    failed: list[RF] | None = None,
    implicit: int = 0,
    purpose_continuity: float = 0.85,
    mission_legibility: float = 1.0,
    invariant_interpretation: float = 0.85,
    interactive_passed: bool = True,
) -> ReconstructabilityDashboardState:
    founder = founder_dependency
    if founder is None:
        founder = max(0.0, 1.0 - steward)
    return ReconstructabilityDashboardState(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=version,
        system_survivability_score=survivability,
        steward_independence_score=steward,
        founder_dependency_index=founder,
        reconstructability_fitness_score=fitness if fitness is not None else survivability,
        constitutional_debt_score=0.1,
        constitutional_risk_score=0.1,
        personal_capacity_continuity=0.8,
        active_threats=threats or [],
        failed_surfaces=failed or [],
        implicit_assumptions_required=implicit,
        purpose_continuity_index=purpose_continuity,
        mission_legibility_score=mission_legibility,
        invariant_interpretation_score=invariant_interpretation,
        mission_fidelity={"interactive_passed": interactive_passed},
    )


def _fitness(
    *,
    fitness_score: float = 0.85,
    stewardship: float = 0.85,
    failed: list[RF] | None = None,
    implicit: int = 0,
) -> ReconstructabilityFitnessState:
    return ReconstructabilityFitnessState(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=1,
        fitness_score=fitness_score,
        stewardship_readiness_score=stewardship,
        failed_surfaces=failed or [],
        implicit_assumptions_required=implicit,
    )


def test_article_s2_registered() -> None:
    article = constitutional_registry.get_article(ARTICLE_S2["id"])
    assert article is not None
    assert "Succession" in article["name"]


def test_succession_ready_requires_all_s2_thresholds() -> None:
    ready = _dashboard(survivability=0.75, steward=0.75, founder_dependency=0.25, fitness=0.75)
    assert succession_ready(ready, _fitness()) is True

    assert succession_ready(_dashboard(founder_dependency=0.35), _fitness()) is False
    assert succession_ready(_dashboard(survivability=0.65), _fitness()) is False
    assert succession_ready(_dashboard(), _fitness(fitness_score=0.5)) is False
    assert succession_ready(_dashboard(), _fitness(failed=[RF.STEWARD_DISCONTINUITY])) is False


def test_succession_preconditions() -> None:
    dashboard = _dashboard()
    pre = evaluate_succession_preconditions(dashboard, _fitness())
    assert pre.all_met is True

    blocked_dashboard = _dashboard(threats=[RF.EVIDENCE_LOSS, RF.AUTHORITY_OPACITY], implicit=2)
    pre_fail = evaluate_succession_preconditions(blocked_dashboard, _fitness())
    assert pre_fail.continuity_intact is False
    assert pre_fail.knowledge_externalized is False


def test_succession_blocked_failure_modes() -> None:
    blocked, reasons = succession_blocked(
        _dashboard(founder_dependency=0.5, threats=[RF.EVIDENCE_LOSS] * 4)
    )
    assert blocked is True
    assert "founder_dependency_too_high" in reasons
    assert "active_rf_threats_red_zone" in reasons


def test_mandatory_succession_tracker(csr: ConstitutionalStateRuntime) -> None:
    high_founder = _dashboard(
        founder_dependency=FOUNDER_DEPENDENCY_MANDATORY_SUCCESSION_THRESHOLD + 0.05,
        version=1,
    )
    for version in range(1, MANDATORY_SUCCESSION_CYCLES + 1):
        dash = high_founder.model_copy(update={"version": version})
        track_mandatory_succession_cycle(csr, dash)

    tracker = load_succession_mandatory_tracker(csr)
    assert tracker.mandatory_triggered is True

    obligations = apply_mandatory_succession_obligations(csr, high_founder)
    assert "prepare_succession_proof" in obligations


def test_mandatory_succession_amendment_trigger(csr: ConstitutionalStateRuntime) -> None:
    dashboard = _dashboard(founder_dependency=0.5)
    opened = apply_dashboard_to_amendment_triggers(
        csr,
        dashboard,
        mandatory_founder_cycles=MANDATORY_SUCCESSION_CYCLES,
    )
    scopes = {record.scope for record in opened}
    assert "succession_readiness" in scopes


def test_survivability_amendment_template_opens(csr: ConstitutionalStateRuntime) -> None:
    dashboard = _dashboard(survivability=0.5, steward=0.5, founder_dependency=0.5)
    record = open_or_escalate_survivability_amendment(csr, dashboard)
    assert record is not None
    assert "SURVIVABILITY REMEDIATION" in record.amendment_type
    loaded = load_survivability_amendment(csr)
    assert loaded is not None
    assert "survivability_below_0.60" in loaded.triggers


def test_survivability_amendment_trigger_evaluation() -> None:
    triggers = evaluate_survivability_amendment_triggers(
        _dashboard(survivability=0.5, founder_dependency=0.5, threats=[RF.EVIDENCE_LOSS] * 4)
    )
    assert "survivability_below_0.60" in triggers
    assert "founder_dependency_above_0.40" in triggers
    assert "active_rf_threats_red_zone" in triggers


def test_maybe_initiate_succession_with_preconditions(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.hiddenness.hiddenness_runtime import HiddennessRuntime, load_hiddenness_state
    from constitutional.runtime.mission_fidelity_interactive import (
        MISSION_FIDELITY_QUESTIONS,
        submit_mission_fidelity_answers,
    )
    from constitutional.runtime.mission_fidelity_runtime import (
        MISSION_FIDELITY_STATE_ID,
        MISSION_STATEMENT_STATE_ID,
        MissionFidelityRuntime,
        MissionStatementState,
        load_mission_fidelity_state,
    )
    from constitutional.runtime.reconstructability_dashboard import build_reconstructability_dashboard
    from constitutional.significance.significance_judgment_runtime import (
        seed_passing_significance_judgment,
    )

    csr.put_domain_doc(
        MISSION_STATEMENT_STATE_ID,
        "mission_statement",
        MissionStatementState(
            text=(
                "Enable independent stewards to reconstruct and operate governed systems "
                "without founder assistance while preserving constitutional meaning."
            ),
            invariant_rationale="Purpose must survive steward discontinuity.",
            founding_context=(
                "Born from observer-reproducible proof requirements and constitutional substrate design."
            ),
        ),
    )
    submit_mission_fidelity_answers(
        csr,
        {
            q.question_id: (
                f"Steward articulation for {q.prompt} — sufficient detail for cold-start continuity."
            )
            for q in MISSION_FIDELITY_QUESTIONS
        },
    )
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
    from constitutional.salience.judgment_runtime import seed_passing_salience_judgment
    from tests.constitutional.test_hiddenness_runtime import _seed_salience_ledger_for_succession

    seed_passing_salience_judgment(csr)
    _seed_salience_ledger_for_succession(csr)
    now = datetime.now(UTC)
    dashboard = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)
    dashboard = dashboard.model_copy(
        update={
            "steward_independence_score": 0.85,
            "system_survivability_score": 0.85,
            "founder_dependency_index": 0.15,
            "reconstructability_fitness_score": 0.85,
            "implicit_assumptions_required": 0,
            "active_threats": [],
        }
    )
    hiddenness = load_hiddenness_state(csr)
    record = maybe_initiate_succession(csr, dashboard, fitness=_fitness())
    assert record is not None
    assert "S-2" in record.article_reference or "Succession" in record.reason
    assert hiddenness.hiddenness_index >= 0.8
