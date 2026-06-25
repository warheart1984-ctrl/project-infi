"""Article S-2 — Succession Protocol Integration (operator orchestration layer)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from constitutional.core.articles import ARTICLE_S2, ARTICLE_S2_REFERENCE
from constitutional.runtime.dashboard_governance import (
    GovernanceGateDecision,
    apply_dashboard_to_governance_gate,
)
from constitutional.runtime.fitness_risk import get_reconstructability_fitness_state
from constitutional.runtime.mission_fidelity_runtime import (
    MissionFidelityState,
    load_mission_fidelity_state,
)
from constitutional.runtime.reconstructability_dashboard import ReconstructabilityDashboardState
from constitutional.runtime.reconstructability_dashboard_runtime import (
    ReconstructabilityDashboardRuntime,
    load_reconstructability_dashboard,
)
from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessState
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.survivability_amendment import (
    SurvivabilityAmendmentRecord,
    amendment_success_criteria_met,
    load_survivability_amendment,
    open_or_escalate_survivability_amendment,
    render_survivability_amendment_template,
)
from constitutional.runtime.survivability_enforcement import (
    FOUNDER_DEPENDENCY_REDUCTION_PHASES,
    THRESHOLD_TABLE,
    ArticleS1Compliance,
    SuccessionReadinessChecklist,
    build_succession_readiness_checklist,
    classify_dashboard_metrics,
    evaluate_article_s1_compliance,
    load_cold_start_schedule,
)
from operator_kernel.succession import (
    SuccessionPreconditions,
    SuccessionProcessRecord,
    SuccessionProof,
    evaluate_succession_preconditions,
    load_succession_mandatory_tracker,
    load_succession_process,
    load_succession_proof,
    mandatory_succession_required,
    succession_blocked,
    succession_ready,
)
from constitutional.significance.significance_judgment_runtime import (
    SignificanceJudgmentState,
    load_significance_judgment_state,
)
from constitutional.eck2.models import ECK2PipelineResult
from constitutional.eck2.runtime import load_eck2_pipeline

__all__ = [
    "ArticleS2IntegrationSnapshot",
    "ArticleS2SuccessionStatus",
    "build_article_s2_integration_snapshot",
]


class ArticleS2SuccessionStatus(BaseModel):
    """S-2 operational status — readiness, blocks, mandatory triggers, open process."""

    article_reference: str = ARTICLE_S2_REFERENCE
    ready: bool = False
    blocked: bool = False
    block_reasons: list[str] = Field(default_factory=list)
    preconditions: SuccessionPreconditions
    mandatory_succession_required: bool = False
    consecutive_high_founder_cycles: int = 0
    process: SuccessionProcessRecord | None = None
    proof: SuccessionProof | None = None
    significance_judgment: SignificanceJudgmentState | None = None
    eck2_pipeline: ECK2PipelineResult | None = None


class ArticleS2IntegrationSnapshot(BaseModel):
    """Unified Article S / S-2 survivability cockpit payload."""

    article_s_reference: str = "Article S — Survivability Doctrine"
    article_s2_reference: str = ARTICLE_S2_REFERENCE
    article_s2_obligations: list[str] = Field(default_factory=lambda: list(ARTICLE_S2["obligations"]))
    evaluated_at: datetime
    dashboard: ReconstructabilityDashboardState
    zones: dict[str, str] = Field(default_factory=dict)
    threshold_table: dict[str, dict[str, float | int]] = Field(
        default_factory=lambda: dict(THRESHOLD_TABLE)
    )
    article_s1: ArticleS1Compliance
    succession: ArticleS2SuccessionStatus
    checklist: SuccessionReadinessChecklist
    governance: GovernanceGateDecision
    survivability_amendment: SurvivabilityAmendmentRecord | None = None
    amendment_template_markdown: str | None = None
    amendment_complete: bool = False
    founder_dependency_reduction_phases: list[dict[str, Any]] = Field(
        default_factory=lambda: list(FOUNDER_DEPENDENCY_REDUCTION_PHASES)
    )
    cold_start_schedule: dict[str, Any] = Field(default_factory=dict)


def _load_fitness(csr: ConstitutionalStateRuntime) -> ReconstructabilityFitnessState | None:
    try:
        return get_reconstructability_fitness_state(csr)
    except KeyError:
        return None


def _resolve_dashboard(
    csr: ConstitutionalStateRuntime,
    *,
    refresh: bool = False,
) -> ReconstructabilityDashboardState:
    if refresh:
        return ReconstructabilityDashboardRuntime(csr).update_snapshot()
    try:
        return load_reconstructability_dashboard(csr)
    except KeyError:
        return ReconstructabilityDashboardRuntime(csr).update_snapshot()


def _load_mf_state(csr: ConstitutionalStateRuntime) -> MissionFidelityState | None:
    try:
        return load_mission_fidelity_state(csr)
    except KeyError:
        return None


def _interactive_passed(dashboard: ReconstructabilityDashboardState) -> bool | None:
    mf = dashboard.mission_fidelity or {}
    if "interactive_passed" in mf:
        return bool(mf["interactive_passed"])
    return None


def build_article_s2_succession_status(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None,
) -> ArticleS2SuccessionStatus:
    mf_state = _load_mf_state(csr)
    interactive = _interactive_passed(dashboard)
    blocked, block_reasons = succession_blocked(
        dashboard,
        fitness,
        mf_state=mf_state,
        interactive_passed=interactive,
        csr=csr,
    )
    tracker = load_succession_mandatory_tracker(csr)
    return ArticleS2SuccessionStatus(
        ready=succession_ready(
            dashboard,
            fitness,
            mf_state=mf_state,
            interactive_passed=interactive,
            csr=csr,
        ),
        blocked=blocked,
        block_reasons=block_reasons,
        preconditions=evaluate_succession_preconditions(dashboard, fitness, csr=csr),
        mandatory_succession_required=mandatory_succession_required(tracker),
        consecutive_high_founder_cycles=tracker.consecutive_high_founder_cycles,
        process=load_succession_process(csr),
        proof=load_succession_proof(csr),
        significance_judgment=load_significance_judgment_state(csr),
        eck2_pipeline=load_eck2_pipeline(csr),
    )


def build_article_s2_integration_snapshot(
    csr: ConstitutionalStateRuntime,
    *,
    refresh: bool = False,
    fitness: ReconstructabilityFitnessState | None = None,
    opened_at: datetime | None = None,
    escalate_amendment: bool = True,
) -> ArticleS2IntegrationSnapshot:
    """Compose Article S-1 metrics, S-2 succession state, checklist, and amendment template."""
    now = opened_at or datetime.now(UTC).replace(microsecond=0)
    dashboard = _resolve_dashboard(csr, refresh=refresh)
    rf_state = fitness if fitness is not None else _load_fitness(csr)

    hiddenness = None
    try:
        from constitutional.hiddenness.hiddenness_runtime import load_hiddenness_state

        hiddenness = load_hiddenness_state(csr)
    except KeyError:
        hiddenness = None

    article_s1 = evaluate_article_s1_compliance(dashboard, rf_state, evaluated_at=now)
    zones = classify_dashboard_metrics(
        dashboard,
        succession_readiness_score=article_s1.succession_readiness_score,
    )
    checklist = build_succession_readiness_checklist(dashboard, rf_state, hiddenness=hiddenness)
    governance = apply_dashboard_to_governance_gate(dashboard)
    succession = build_article_s2_succession_status(csr, dashboard, rf_state)

    amendment: SurvivabilityAmendmentRecord | None = None
    if escalate_amendment and article_s1.constitutional_breach:
        amendment = open_or_escalate_survivability_amendment(
            csr, dashboard, fitness=rf_state, opened_at=now
        )
    if amendment is None:
        amendment = load_survivability_amendment(csr)

    template_md: str | None = None
    if amendment is not None and amendment.status == "open":
        template_md = render_survivability_amendment_template(amendment)

    schedule = load_cold_start_schedule(csr)

    return ArticleS2IntegrationSnapshot(
        evaluated_at=now,
        dashboard=dashboard,
        zones={key: zone.value for key, zone in zones.items()},
        article_s1=article_s1,
        succession=succession,
        checklist=checklist,
        governance=governance,
        survivability_amendment=amendment,
        amendment_template_markdown=template_md,
        amendment_complete=amendment_success_criteria_met(dashboard),
        cold_start_schedule=schedule.model_dump(mode="json"),
    )
