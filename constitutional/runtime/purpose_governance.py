"""Article P purpose continuity governance — gates high-impact actions and succession."""

from __future__ import annotations

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_P_REFERENCE,
    INVARIANT_INTERPRETATION_SUCCESS_SCORE,
    MISSION_LEGIBILITY_MIN_SCORE,
    PURPOSE_CONTINUITY_INDEX_THRESHOLD,
    RED_ZONE_PF_THREAT_COUNT,
)
from constitutional.hiddenness.hiddenness_runtime import HiddennessState, load_hiddenness_state
from constitutional.runtime.mission_fidelity_interactive import load_mission_fidelity_interactive
from constitutional.runtime.mission_fidelity_runtime import (
    MissionFidelityState,
    load_mission_fidelity_state,
)
from constitutional.runtime.purpose_failures import PurposeFailureClass as PF
from constitutional.runtime.reconstructability_dashboard import ReconstructabilityDashboardState


class ArticlePCompliance(BaseModel):
    purpose_continuity_index: float = Field(ge=0.0, le=1.0)
    mission_legibility_score: float = Field(ge=0.0, le=1.0)
    invariant_interpretation_score: float = Field(ge=0.0, le=1.0)
    purpose_threat_count: int = Field(ge=0)
    purpose_red_zone: bool = False
    interactive_passed: bool = False
    hidden_item_count: int = Field(default=0, ge=0)
    constitutional_breach: bool = False
    block_reasons: list[str] = Field(default_factory=list)


def purpose_in_red_zone(purpose_threats: list[PF]) -> bool:
    return len(purpose_threats) >= RED_ZONE_PF_THREAT_COUNT


def evaluate_article_p_compliance(
    dashboard: ReconstructabilityDashboardState,
    *,
    mf_state: MissionFidelityState | None = None,
    hiddenness: HiddennessState | None = None,
) -> ArticlePCompliance:
    pci = dashboard.purpose_continuity_index
    legibility = dashboard.mission_legibility_score
    interpretation = dashboard.invariant_interpretation_score
    threats = list(dashboard.purpose_threats)
    red_zone = purpose_in_red_zone(threats)

    interactive = load_mission_fidelity_interactive_from_dashboard(dashboard)
    hidden_count = hiddenness.hidden_items.__len__() if hiddenness else 0

    block_reasons: list[str] = []
    if pci < PURPOSE_CONTINUITY_INDEX_THRESHOLD:
        block_reasons.append("purpose_continuity_index_below_threshold")
    if legibility < MISSION_LEGIBILITY_MIN_SCORE:
        block_reasons.append("mission_legibility_below_minimum")
    if interpretation < INVARIANT_INTERPRETATION_SUCCESS_SCORE:
        block_reasons.append("invariant_interpretation_below_success_threshold")
    if red_zone:
        block_reasons.append("purpose_threats_in_red_zone")

    breach = bool(block_reasons)

    return ArticlePCompliance(
        purpose_continuity_index=pci,
        mission_legibility_score=legibility,
        invariant_interpretation_score=interpretation,
        purpose_threat_count=len(threats),
        purpose_red_zone=red_zone,
        interactive_passed=interactive,
        hidden_item_count=hidden_count,
        constitutional_breach=breach,
        block_reasons=block_reasons,
    )


def load_mission_fidelity_interactive_from_dashboard(
    dashboard: ReconstructabilityDashboardState,
) -> bool:
    """Interactive pass is stored on dashboard mission_fidelity dict when available."""
    mf = dashboard.mission_fidelity or {}
    if "interactive_passed" in mf:
        return bool(mf["interactive_passed"])
    return False


def purpose_blocks_governance(
    dashboard: ReconstructabilityDashboardState,
    compliance: ArticlePCompliance | None = None,
) -> tuple[bool, list[str]]:
    """P-1 — block high-impact actions when purpose continuity is in breach."""
    article_p = compliance or evaluate_article_p_compliance(dashboard)
    return article_p.constitutional_breach, list(article_p.block_reasons)


def succession_purpose_ready(
    dashboard: ReconstructabilityDashboardState,
    *,
    mf_state: MissionFidelityState | None = None,
    interactive_passed: bool | None = None,
) -> tuple[bool, list[str]]:
    """Article P succession preconditions — steward must articulate purpose without founder."""
    reasons: list[str] = []

    if dashboard.purpose_continuity_index < PURPOSE_CONTINUITY_INDEX_THRESHOLD:
        reasons.append("purpose_continuity_index_below_threshold")

    if dashboard.mission_legibility_score < MISSION_LEGIBILITY_MIN_SCORE:
        reasons.append("mission_legibility_fails")

    if dashboard.invariant_interpretation_score < INVARIANT_INTERPRETATION_SUCCESS_SCORE:
        reasons.append("invariant_interpretation_below_success")

    if purpose_in_red_zone(dashboard.purpose_threats):
        reasons.append("purpose_threats_in_red_zone")

    passed = interactive_passed
    if passed is None:
        passed = load_mission_fidelity_interactive_from_dashboard(dashboard)
    if not passed:
        reasons.append("mission_fidelity_interactive_not_passed")

    if mf_state is not None and mf_state.failed_surfaces:
        reasons.append("mission_fidelity_test_has_failed_surfaces")

    return not reasons, reasons


def load_compliance_from_csr(
    csr,
    dashboard: ReconstructabilityDashboardState,
) -> ArticlePCompliance:
    mf_state: MissionFidelityState | None = None
    hiddenness: HiddennessState | None = None
    try:
        mf_state = load_mission_fidelity_state(csr)
    except KeyError:
        pass
    try:
        hiddenness = load_hiddenness_state(csr)
    except KeyError:
        pass
    interactive = load_mission_fidelity_interactive(csr)
    compliance = evaluate_article_p_compliance(dashboard, mf_state=mf_state, hiddenness=hiddenness)
    if interactive is not None:
        compliance = compliance.model_copy(update={"interactive_passed": interactive.interactive_passed})
    return compliance
