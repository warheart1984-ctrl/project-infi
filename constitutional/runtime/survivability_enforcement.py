"""Article S-1 implementation — survivability thresholds, zones, and compliance."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_S_INVARIANT,
    ARTICLE_S_REFERENCE,
    FOUNDER_DEPENDENCY_AMENDMENT_THRESHOLD,
    RED_ZONE_RF_THREAT_COUNT,
    STEWARD_INDEPENDENCE_AMENDMENT_THRESHOLD,
    SURVIVABILITY_AMENDMENT_COMPLETE_FITNESS,
    SURVIVABILITY_AMENDMENT_SCORE_THRESHOLD,
)
from constitutional.runtime.reconstructability_dashboard import ReconstructabilityDashboardState
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessState
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.survivability_amendment import (
    cold_start_steward_passes,
    fitness_passes,
)

# S-1.2 — mandatory fitness assessment interval (default 6h)
FITNESS_ASSESSMENT_INTERVAL_HOURS = 6
FITNESS_ASSESSMENT_INTERVAL = timedelta(hours=FITNESS_ASSESSMENT_INTERVAL_HOURS)

# S-1.3 — cold-start steward test minimum cadence
COLD_START_TEST_INTERVAL_DAYS = 7
COLD_START_TEST_INTERVAL = timedelta(days=COLD_START_TEST_INTERVAL_DAYS)

COLD_START_SCHEDULE_STATE_ID = "survivability_cold_start_schedule__latest"


class SurvivabilityZone(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


# Survivability Threshold Table (v0) — constitutionally enforced
THRESHOLD_TABLE: dict[str, dict[str, float | int]] = {
    "system_survivability_score": {"green_min": 0.70, "yellow_min": 0.60},
    "steward_independence_score": {"green_min": 0.70, "yellow_min": 0.60},
    "founder_dependency_index": {"green_max": 0.30, "yellow_max": 0.40},
    "reconstructability_fitness_score": {"green_min": 0.70, "yellow_min": 0.50},
    "cold_start_steward_assumptions": {"green_max": 1, "yellow_max": 3},
    "active_rf_threat_surfaces": {"green_max": 1, "yellow_max": 3},
    "succession_readiness_score": {"green_min": 0.70, "yellow_min": 0.60},
}


def classify_higher_is_better(value: float, *, green_min: float, yellow_min: float) -> SurvivabilityZone:
    if value >= green_min:
        return SurvivabilityZone.GREEN
    if value >= yellow_min:
        return SurvivabilityZone.YELLOW
    return SurvivabilityZone.RED


def classify_lower_is_better(value: float, *, green_max: float, yellow_max: float) -> SurvivabilityZone:
    if value <= green_max:
        return SurvivabilityZone.GREEN
    if value <= yellow_max:
        return SurvivabilityZone.YELLOW
    return SurvivabilityZone.RED


def classify_count_lower_is_better(count: int, *, green_max: int, yellow_max: int) -> SurvivabilityZone:
    if count <= green_max:
        return SurvivabilityZone.GREEN
    if count <= yellow_max:
        return SurvivabilityZone.YELLOW
    return SurvivabilityZone.RED


def classify_dashboard_metrics(
    dashboard: ReconstructabilityDashboardState,
    *,
    succession_readiness_score: float | None = None,
) -> dict[str, SurvivabilityZone]:
    """Map dashboard fields to Green / Yellow / Red zones per S-1 threshold table."""
    sr_score = succession_readiness_score
    if sr_score is None:
        sr_score = compute_succession_readiness_score(dashboard)

    return {
        "system_survivability_score": classify_higher_is_better(
            dashboard.system_survivability_score,
            green_min=0.70,
            yellow_min=0.60,
        ),
        "steward_independence_score": classify_higher_is_better(
            dashboard.steward_independence_score,
            green_min=0.70,
            yellow_min=0.60,
        ),
        "founder_dependency_index": classify_lower_is_better(
            dashboard.founder_dependency_index,
            green_max=0.30,
            yellow_max=0.40,
        ),
        "reconstructability_fitness_score": classify_higher_is_better(
            dashboard.reconstructability_fitness_score,
            green_min=0.70,
            yellow_min=0.50,
        ),
        "cold_start_steward_assumptions": classify_count_lower_is_better(
            dashboard.implicit_assumptions_required,
            green_max=1,
            yellow_max=3,
        ),
        "active_rf_threat_surfaces": classify_count_lower_is_better(
            len(dashboard.active_threats),
            green_max=1,
            yellow_max=3,
        ),
        "succession_readiness_score": classify_higher_is_better(
            sr_score,
            green_min=0.70,
            yellow_min=0.60,
        ),
    }


def compute_succession_readiness_score(
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
) -> float:
    """Aggregate succession readiness from Article S checklist dimensions (v0)."""
    zones = {
        "system_survivability_score": classify_higher_is_better(
            dashboard.system_survivability_score, green_min=0.70, yellow_min=0.60
        ),
        "steward_independence_score": classify_higher_is_better(
            dashboard.steward_independence_score, green_min=0.70, yellow_min=0.60
        ),
        "founder_dependency_index": classify_lower_is_better(
            dashboard.founder_dependency_index, green_max=0.30, yellow_max=0.40
        ),
        "reconstructability_fitness_score": classify_higher_is_better(
            dashboard.reconstructability_fitness_score, green_min=0.70, yellow_min=0.50
        ),
        "cold_start_steward_assumptions": classify_count_lower_is_better(
            dashboard.implicit_assumptions_required, green_max=1, yellow_max=3
        ),
        "active_rf_threat_surfaces": classify_count_lower_is_better(
            len(dashboard.active_threats), green_max=1, yellow_max=3
        ),
    }
    zone_scores = {
        SurvivabilityZone.GREEN: 1.0,
        SurvivabilityZone.YELLOW: 0.65,
        SurvivabilityZone.RED: 0.0,
    }

    metric_score = sum(zone_scores[z] for z in zones.values()) / len(zones)

    checklist_bonus = 0.0
    if cold_start_steward_passes(dashboard, fitness):
        checklist_bonus += 0.15
    if fitness_passes(dashboard, fitness, min_score=SURVIVABILITY_AMENDMENT_COMPLETE_FITNESS):
        checklist_bonus += 0.15
    if RF.STEWARD_DISCONTINUITY not in dashboard.active_threats:
        checklist_bonus += 0.10
    if dashboard.implicit_assumptions_required == 0:
        checklist_bonus += 0.10

    return min(1.0, 0.5 * metric_score + checklist_bonus)


class ArticleS1Compliance(BaseModel):
    """S-1.1 — governed invariant compliance snapshot."""

    article_reference: str = ARTICLE_S_REFERENCE
    governed_invariant: str = ARTICLE_S_INVARIANT
    evaluated_at: datetime
    compliant: bool
    breach_reasons: list[str] = Field(default_factory=list)
    zones: dict[str, str] = Field(default_factory=dict)
    succession_readiness_score: float = Field(ge=0.0, le=1.0)
    constitutional_breach: bool = False


def evaluate_article_s1_compliance(
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
    *,
    evaluated_at: datetime | None = None,
) -> ArticleS1Compliance:
    """S-1.1 — survivability, steward independence, and founder dependency are constitutional."""
    now = evaluated_at or dashboard.snapshot_at
    sr_score = compute_succession_readiness_score(dashboard, fitness)
    zones = classify_dashboard_metrics(dashboard, succession_readiness_score=sr_score)
    zone_labels = {key: zone.value for key, zone in zones.items()}

    breach_reasons: list[str] = []
    if dashboard.system_survivability_score < SURVIVABILITY_AMENDMENT_SCORE_THRESHOLD:
        breach_reasons.append("system_survivability_below_0.60")
    if dashboard.steward_independence_score < STEWARD_INDEPENDENCE_AMENDMENT_THRESHOLD:
        breach_reasons.append("steward_independence_below_0.60")
    if dashboard.founder_dependency_index > FOUNDER_DEPENDENCY_AMENDMENT_THRESHOLD:
        breach_reasons.append("founder_dependency_above_0.40")

    red_metrics = [name for name, zone in zones.items() if zone == SurvivabilityZone.RED]
    constitutional_breach = bool(breach_reasons) or bool(red_metrics)

    return ArticleS1Compliance(
        evaluated_at=now,
        compliant=not constitutional_breach,
        breach_reasons=breach_reasons,
        zones=zone_labels,
        succession_readiness_score=sr_score,
        constitutional_breach=constitutional_breach,
    )


class SuccessionReadinessChecklist(BaseModel):
    """Succession Readiness Checklist (v0) — operational test for Article S."""

    reconstructability: dict[str, bool] = Field(default_factory=dict)
    steward_capability: dict[str, bool] = Field(default_factory=dict)
    authority_transfer: dict[str, bool] = Field(default_factory=dict)
    knowledge_transfer: dict[str, bool] = Field(default_factory=dict)
    hiddenness: dict[str, bool] = Field(default_factory=dict)
    constitutional_health: dict[str, bool] = Field(default_factory=dict)

    @property
    def all_pass(self) -> bool:
        sections = (
            self.reconstructability,
            self.steward_capability,
            self.authority_transfer,
            self.knowledge_transfer,
            self.hiddenness,
            self.constitutional_health,
        )
        return all(all(section.values()) for section in sections)


def build_succession_readiness_checklist(
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
    *,
    hiddenness: HiddennessState | None = None,
) -> SuccessionReadinessChecklist:
    """Evaluate checklist items from current dashboard and fitness state."""
    from constitutional.core.articles import SUCCESSION_MIN_HIDDENNESS_INDEX
    from constitutional.runtime.hiddenness_governance import (
        hiddenness_in_red_zone,
        hiddenness_runtime_passes,
        succession_hiddenness_ready,
    )

    lineage_threats = {RF.EVIDENCE_LOSS, RF.LINEAGE_BREAK}
    authority_threats = {RF.AUTHORITY_OPACITY, RF.ACCOUNTABILITY_EROSION}
    red_zone_clear = len(dashboard.active_threats) < RED_ZONE_RF_THREAT_COUNT

    fitness_ok = fitness_passes(
        dashboard, fitness, min_score=SURVIVABILITY_AMENDMENT_COMPLETE_FITNESS
    )
    cold_start_ok = cold_start_steward_passes(dashboard, fitness)
    hiddenness_ok, _ = succession_hiddenness_ready(dashboard, hiddenness=hiddenness)
    hidden_threats = (
        list(hiddenness.failed_surfaces) if hiddenness is not None else list(dashboard.hidden_threats)
    )

    return SuccessionReadinessChecklist(
        reconstructability={
            "historical_state_reconstructable": fitness_ok,
            "decisions_replayable": fitness_ok,
            "authority_chains_traceable": not any(
                t in dashboard.active_threats for t in authority_threats
            ),
            "amendment_lineage_complete": RF.LINEAGE_BREAK not in dashboard.active_threats,
            "semantic_definitions_stable": RF.SEMANTIC_DRIFT not in dashboard.failed_surfaces,
            "no_red_zone_rf_threats": red_zone_clear,
        },
        steward_capability={
            "operate_core_runtimes": cold_start_ok,
            "execute_governed_actions": dashboard.steward_independence_score >= 0.60,
            "interpret_invariants": fitness_ok,
            "perform_remediation": dashboard.system_survivability_score >= 0.60,
            "evaluate_amendments": RF.BOUNDARY_CONFUSION not in dashboard.failed_surfaces,
        },
        authority_transfer={
            "authority_chain_explicit": RF.AUTHORITY_OPACITY not in dashboard.active_threats,
            "delegation_contracts_valid": RF.ACCOUNTABILITY_EROSION not in dashboard.active_threats,
            "no_founder_exclusive_authority": dashboard.founder_dependency_index <= 0.40,
        },
        knowledge_transfer={
            "operational_knowledge_externalized": dashboard.implicit_assumptions_required <= 1,
            "architectural_knowledge_externalized": dashboard.implicit_assumptions_required == 0,
            "decision_rationale_externalized": RF.EVIDENCE_LOSS not in dashboard.active_threats,
            "no_founder_only_mental_models": dashboard.implicit_assumptions_required == 0,
        },
        hiddenness={
            "hiddenness_runtime_passes": hiddenness_runtime_passes(
                hiddenness,
                min_index=SUCCESSION_MIN_HIDDENNESS_INDEX,
            ),
            "hiddenness_index_at_succession_threshold": (
                (hiddenness.hiddenness_index if hiddenness else dashboard.hiddenness_index)
                >= SUCCESSION_MIN_HIDDENNESS_INDEX
            ),
            "no_hf_red_zone": not hiddenness_in_red_zone(hidden_threats),
            "no_implicit_assumptions": not (
                hiddenness.implicit_assumptions if hiddenness else dashboard.implicit_assumptions
            ),
            "no_undocumented_invariants": not (
                hiddenness.undocumented_invariants if hiddenness else dashboard.undocumented_invariants
            ),
            "no_undocumented_purpose_fragments": not (
                hiddenness.undocumented_purpose_fragments
                if hiddenness
                else dashboard.undocumented_purpose_fragments
            ),
            "no_implicit_authority": not (
                hiddenness.undocumented_authority if hiddenness else dashboard.undocumented_authority
            ),
            "no_founder_only_knowledge": not (
                hiddenness.founder_only_knowledge if hiddenness else dashboard.founder_only_knowledge
            ),
            "cold_start_hiddenness_section_passes": hiddenness_ok,
        },
        constitutional_health={
            "survivability_green": dashboard.system_survivability_score >= 0.70,
            "steward_independence_green": dashboard.steward_independence_score >= 0.70,
            "founder_dependency_green": dashboard.founder_dependency_index <= 0.30,
            "fitness_green": dashboard.reconstructability_fitness_score >= 0.70,
            "personal_state_stable": dashboard.personal_capacity_continuity >= 0.60,
        },
    )


FOUNDER_DEPENDENCY_REDUCTION_PHASES: list[dict[str, Any]] = [
    {
        "phase": 1,
        "name": "Externalize Knowledge",
        "goal": "Reduce implicit assumptions required in Cold-Start Test",
        "items": [
            "Convert implicit architectural knowledge into receipts or documents",
            "Externalize invariants, schemas, and decision rationale",
            "Externalize runtime operation guides",
            "Externalize amendment logic and governance gates",
            "Externalize continuity and lineage interpretation",
        ],
    },
    {
        "phase": 2,
        "name": "Transfer Authority",
        "goal": "Founder is no longer a single point of governance",
        "items": [
            "Remove founder-exclusive authority chains",
            "Replace implicit authority with explicit delegation receipts",
            "Ensure accountable_party is not founder-only",
            "Add multi-steward authority paths",
        ],
    },
    {
        "phase": 3,
        "name": "Replicate Stewardship Capability",
        "goal": "Stewardship becomes reproducible",
        "items": [
            "Train at least one alternate steward",
            "Validate via Cold-Start Test",
            "Validate via Fitness replay",
            "Validate via amendment evaluation",
        ],
    },
    {
        "phase": 4,
        "name": "Reduce Operational Load",
        "goal": "Founder not required for day-to-day operation",
        "items": [
            "Automate routine governance checks",
            "Automate ledger integrity checks",
            "Automate continuity traces",
            "Automate risk and debt updates",
            "Automate survivability dashboard generation",
        ],
    },
    {
        "phase": 5,
        "name": "Succession Simulation",
        "goal": "Prove the system can survive its creators",
        "items": [
            "Run full founder-disappears simulation",
            "New steward operates 24-72 hours",
            "All actions receipted",
            "All failures logged",
            "Survivability Score recalculated",
        ],
    },
    {
        "phase": 6,
        "name": "Constitutional Lock-In",
        "goal": "Survivability becomes permanent constitutional obligation",
        "items": [
            "Lock survivability thresholds into Article S",
            "Lock Cold-Start Test into mandatory governance",
            "Lock Fitness Runtime into constitutional heartbeat",
            "Lock succession readiness into governance gate",
        ],
    },
]


class ColdStartScheduleState(BaseModel):
    state_id: str = COLD_START_SCHEDULE_STATE_ID
    state_type: str = "survivability_cold_start_schedule"
    last_run_at: datetime | None = None
    last_founder_dependency_index: float = Field(default=0.0, ge=0.0, le=1.0)
    founder_dependency_increased: bool = False
    due_reason: str | None = None


def load_cold_start_schedule(csr: ConstitutionalStateRuntime) -> ColdStartScheduleState:
    try:
        doc = csr.get_domain_doc(COLD_START_SCHEDULE_STATE_ID, ColdStartScheduleState)
        assert isinstance(doc, ColdStartScheduleState)
        return doc
    except KeyError:
        return ColdStartScheduleState()


def save_cold_start_schedule(csr: ConstitutionalStateRuntime, state: ColdStartScheduleState) -> None:
    csr.put_domain_doc(COLD_START_SCHEDULE_STATE_ID, "survivability_cold_start_schedule", state)


def cold_start_test_due(
    schedule: ColdStartScheduleState,
    dashboard: ReconstructabilityDashboardState,
    *,
    now: datetime | None = None,
    force: bool = False,
) -> tuple[bool, str | None]:
    """S-1.3 — determine if a Cold-Start Steward Test must run."""
    if force:
        return True, "forced"

    clock = now or dashboard.snapshot_at
    if schedule.last_run_at is None:
        return True, "initial"

    elapsed = clock - schedule.last_run_at
    if elapsed >= COLD_START_TEST_INTERVAL:
        return True, "weekly"

    if dashboard.founder_dependency_index > schedule.last_founder_dependency_index + 0.05:
        return True, "founder_dependency_increased"

    return False, None


def record_cold_start_run(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
    *,
    run_at: datetime | None = None,
    reason: str | None = None,
) -> ColdStartScheduleState:
    now = run_at or dashboard.snapshot_at
    state = load_cold_start_schedule(csr)
    state.last_run_at = now
    state.last_founder_dependency_index = dashboard.founder_dependency_index
    state.founder_dependency_increased = reason == "founder_dependency_increased"
    state.due_reason = reason
    save_cold_start_schedule(csr, state)
    return state
