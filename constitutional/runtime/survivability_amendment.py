"""Survivability remediation amendment template (UGR-AMENDMENT-S-SURVIVABILITY-v0)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_S2_REFERENCE,
    ARTICLE_S_INVARIANT,
    ARTICLE_S_REFERENCE,
    FOUNDER_DEPENDENCY_AMENDMENT_THRESHOLD,
    RED_ZONE_RF_THREAT_COUNT,
    STEWARD_INDEPENDENCE_AMENDMENT_THRESHOLD,
    SURVIVABILITY_AMENDMENT_COMPLETE_FITNESS,
    SURVIVABILITY_AMENDMENT_COMPLETE_FOUNDER_MAX,
    SURVIVABILITY_AMENDMENT_COMPLETE_STEWARD,
    SURVIVABILITY_AMENDMENT_COMPLETE_SURVIVABILITY,
    SURVIVABILITY_AMENDMENT_SCORE_THRESHOLD,
    SURVIVABILITY_AMENDMENT_TEMPLATE_ID,
)
from constitutional.runtime.reconstructability_dashboard import ReconstructabilityDashboardState
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessState
from constitutional.runtime.runtime import ConstitutionalStateRuntime

SURVIVABILITY_AMENDMENT_STATE_ID = "survivability_amendment__pending"


class SurvivabilityAmendmentRecord(BaseModel):
    template_id: str = SURVIVABILITY_AMENDMENT_TEMPLATE_ID
    amendment_type: str = "SURVIVABILITY REMEDIATION AMENDMENT"
    opened_at: datetime
    reason: str
    triggers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    required_actions: list[str] = Field(default_factory=list)
    success_criteria: dict[str, float] = Field(default_factory=dict)
    constitutional_linkage: list[str] = Field(default_factory=list)
    telic_statement: str = (
        "A system is legitimate only if it can survive its creators. "
        "This amendment restores that legitimacy."
    )
    status: str = "open"


DEFAULT_REQUIRED_ACTIONS = [
    "Knowledge Externalization",
    "Authority Transfer",
    "Steward Capability Replication",
    "Operational Automation",
    "Continuity Reinforcement",
]

DEFAULT_CONSTITUTIONAL_LINKAGE = [
    ARTICLE_S_REFERENCE,
    "Article S-1 — Implementation Notes",
    ARTICLE_S2_REFERENCE,
    "Article R — Reconstructability Law",
]


def cold_start_steward_passes(
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
    *,
    csr: ConstitutionalStateRuntime | None = None,
) -> bool:
    """Cold-Start Steward Test passes when R-F8 is clear, no implicit assumptions, and Section 6 passes."""
    if fitness is not None:
        base_ok = (
            RF.STEWARD_DISCONTINUITY not in fitness.failed_surfaces
            and fitness.implicit_assumptions_required == 0
        )
    else:
        base_ok = (
            RF.STEWARD_DISCONTINUITY not in dashboard.failed_surfaces
            and dashboard.implicit_assumptions_required == 0
        )
    if not base_ok:
        return False

    if csr is not None:
        from constitutional.hiddenness.cold_start_hiddenness import cold_start_hiddenness_passes

        ok, _ = cold_start_hiddenness_passes(csr)
        return ok

    return len(dashboard.hidden_threats) == 0


def fitness_passes(
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
    *,
    min_score: float = SURVIVABILITY_AMENDMENT_COMPLETE_FITNESS,
) -> bool:
    score = fitness.fitness_score if fitness is not None else dashboard.reconstructability_fitness_score
    if fitness is not None:
        return score >= min_score and len(fitness.failed_surfaces) == 0
    return score >= min_score and len(dashboard.failed_surfaces) == 0


def evaluate_survivability_amendment_triggers(
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
) -> list[str]:
    """Return trigger reasons that demand a survivability remediation amendment."""
    triggers: list[str] = []

    if dashboard.system_survivability_score < SURVIVABILITY_AMENDMENT_SCORE_THRESHOLD:
        triggers.append("survivability_below_0.60")

    if dashboard.steward_independence_score < STEWARD_INDEPENDENCE_AMENDMENT_THRESHOLD:
        triggers.append("steward_independence_below_0.60")

    if dashboard.founder_dependency_index > FOUNDER_DEPENDENCY_AMENDMENT_THRESHOLD:
        triggers.append("founder_dependency_above_0.40")

    if not fitness_passes(dashboard, fitness, min_score=SURVIVABILITY_AMENDMENT_COMPLETE_FITNESS):
        triggers.append("fitness_failure")

    if not cold_start_steward_passes(dashboard, fitness):
        triggers.append("cold_start_failure")

    if len(dashboard.active_threats) >= RED_ZONE_RF_THREAT_COUNT:
        triggers.append("active_rf_threats_red_zone")

    return triggers


def build_survivability_amendment_record(
    dashboard: ReconstructabilityDashboardState,
    *,
    triggers: list[str],
    fitness: ReconstructabilityFitnessState | None = None,
    opened_at: datetime | None = None,
) -> SurvivabilityAmendmentRecord:
    now = opened_at or datetime.now(UTC).replace(microsecond=0)
    evidence: dict[str, Any] = {
        "dashboard": dashboard.model_dump(mode="json"),
    }
    if fitness is not None:
        evidence["fitness"] = fitness.model_dump(mode="json")

    return SurvivabilityAmendmentRecord(
        opened_at=now,
        reason=(
            f"The system is in violation of {ARTICLE_S_REFERENCE}. "
            "Survivability metrics indicate the system cannot continue without founder intervention."
        ),
        triggers=triggers,
        evidence=evidence,
        required_actions=list(DEFAULT_REQUIRED_ACTIONS),
        success_criteria={
            "survivability_score": SURVIVABILITY_AMENDMENT_COMPLETE_SURVIVABILITY,
            "steward_independence_score": SURVIVABILITY_AMENDMENT_COMPLETE_STEWARD,
            "founder_dependency_index_max": SURVIVABILITY_AMENDMENT_COMPLETE_FOUNDER_MAX,
            "fitness_score": SURVIVABILITY_AMENDMENT_COMPLETE_FITNESS,
            "cold_start_passes": 1.0,
            "red_zone_rf_threats": 0.0,
        },
        constitutional_linkage=list(DEFAULT_CONSTITUTIONAL_LINKAGE),
    )


def load_survivability_amendment(csr: ConstitutionalStateRuntime) -> SurvivabilityAmendmentRecord | None:
    try:
        doc = csr.get_domain_doc(SURVIVABILITY_AMENDMENT_STATE_ID, SurvivabilityAmendmentRecord)
        assert isinstance(doc, SurvivabilityAmendmentRecord)
        return doc
    except KeyError:
        return None


def open_or_escalate_survivability_amendment(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
    *,
    fitness: ReconstructabilityFitnessState | None = None,
    opened_at: datetime | None = None,
) -> SurvivabilityAmendmentRecord | None:
    """Open survivability remediation amendment when template triggers fire."""
    trigger_reasons = evaluate_survivability_amendment_triggers(dashboard, fitness)
    if not trigger_reasons:
        return None

    record = build_survivability_amendment_record(
        dashboard,
        triggers=trigger_reasons,
        fitness=fitness,
        opened_at=opened_at,
    )
    existing = load_survivability_amendment(csr)
    if existing is not None and existing.status == "open":
        merged = list(dict.fromkeys(existing.triggers + record.triggers))
        existing.triggers = merged
        existing.evidence = record.evidence
        csr.put_domain_doc(SURVIVABILITY_AMENDMENT_STATE_ID, "survivability_amendment", existing)
        return existing

    csr.put_domain_doc(SURVIVABILITY_AMENDMENT_STATE_ID, "survivability_amendment", record)
    return record


def amendment_success_criteria_met(dashboard: ReconstructabilityDashboardState) -> bool:
    """True when dashboard satisfies survivability amendment completion thresholds."""
    return (
        dashboard.system_survivability_score >= SURVIVABILITY_AMENDMENT_COMPLETE_SURVIVABILITY
        and dashboard.steward_independence_score >= SURVIVABILITY_AMENDMENT_COMPLETE_STEWARD
        and dashboard.founder_dependency_index <= SURVIVABILITY_AMENDMENT_COMPLETE_FOUNDER_MAX
        and dashboard.reconstructability_fitness_score >= SURVIVABILITY_AMENDMENT_COMPLETE_FITNESS
        and cold_start_steward_passes(dashboard)
        and len(dashboard.active_threats) < RED_ZONE_RF_THREAT_COUNT
    )


def render_survivability_amendment_template(record: SurvivabilityAmendmentRecord) -> str:
    """Render UGR-AMENDMENT-S-SURVIVABILITY-v0 as steward-facing markdown."""
    criteria_lines = "\n".join(
        f"| {key.replace('_', ' ').title()} | {value} |"
        for key, value in record.success_criteria.items()
    )
    trigger_lines = "\n".join(f"- `{trigger}`" for trigger in record.triggers)
    action_lines = "\n".join(f"- [ ] {action}" for action in record.required_actions)
    linkage_lines = "\n".join(f"- {link}" for link in record.constitutional_linkage)

    return f"""# {record.amendment_type}

**Template:** `{record.template_id}`  
**Status:** {record.status.upper()}  
**Opened:** {record.opened_at.isoformat()}

## Constitutional basis

{linkage_lines}

> {record.telic_statement}

## Reason

{record.reason}

## Triggers (constitutional breach)

{trigger_lines}

## Required structural remediation

{action_lines}

## Success criteria (amendment remains open until all met)

| Criterion | Target |
|-----------|--------|
{criteria_lines}

## Governance effect

While this amendment is **open**:

- High-impact missions are blocked when Article S-1 thresholds are breached
- Succession events require fitness assessment and checklist pass
- Amendment process must remain open until survivability is restored to green band

## Evidence snapshot

Dashboard and fitness evidence are receipted in `evidence.dashboard` / `evidence.fitness`.
"""
