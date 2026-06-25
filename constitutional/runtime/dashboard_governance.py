"""Dashboard governance gate — Article S, P, and H constitutional thresholds."""

from __future__ import annotations

from pydantic import BaseModel

from constitutional.core.articles import (
    ARTICLE_H_REFERENCE,
    ARTICLE_P_REFERENCE,
    ARTICLE_S_REFERENCE,
    FOUNDER_DEPENDENCY_BLOCK_THRESHOLD,
    FOUNDER_DEPENDENCY_WARN_THRESHOLD,
    STEWARD_INDEPENDENCE_BLOCK_THRESHOLD,
    STEWARD_INDEPENDENCE_WARN_THRESHOLD,
    SURVIVABILITY_BLOCK_THRESHOLD,
    SURVIVABILITY_WARN_THRESHOLD,
)
from constitutional.runtime.hiddenness_governance import (
    ArticleHCompliance,
    evaluate_article_h_compliance,
    load_article_h_compliance_from_csr,
)
from constitutional.runtime.purpose_governance import (
    ArticlePCompliance,
    evaluate_article_p_compliance,
    load_compliance_from_csr,
)
from constitutional.runtime.reconstructability_dashboard import (
    DASHBOARD_STATE_ID,
    ReconstructabilityDashboardState,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.survivability_enforcement import (
    ArticleS1Compliance,
    evaluate_article_s1_compliance,
)

DASHBOARD_GOVERNANCE_STATE_ID = "dashboard_governance_gate__latest"


class GovernanceGateDecision(BaseModel):
    allow: bool
    level: str  # "ok" | "warn" | "block"
    reason: str
    article_s1: ArticleS1Compliance | None = None
    article_p: ArticlePCompliance | None = None
    article_h: ArticleHCompliance | None = None


def apply_dashboard_to_governance_gate(
    dashboard: ReconstructabilityDashboardState,
    *,
    article_p: ArticlePCompliance | None = None,
    article_h: ArticleHCompliance | None = None,
) -> GovernanceGateDecision:
    """S-1.1, P-1, and H-1 — constitutional thresholds are mandatory, not advisory."""
    compliance = evaluate_article_s1_compliance(dashboard)
    purpose = article_p or evaluate_article_p_compliance(dashboard)
    hiddenness = article_h or evaluate_article_h_compliance(dashboard)

    if hiddenness.constitutional_breach:
        reasons = ", ".join(hiddenness.block_reasons)
        return GovernanceGateDecision(
            allow=False,
            level="block",
            reason=f"Hiddenness breach ({ARTICLE_H_REFERENCE}): {reasons}.",
            article_s1=compliance,
            article_p=purpose,
            article_h=hiddenness,
        )

    if purpose.constitutional_breach:
        reasons = ", ".join(purpose.block_reasons)
        return GovernanceGateDecision(
            allow=False,
            level="block",
            reason=f"Purpose continuity breach ({ARTICLE_P_REFERENCE}): {reasons}.",
            article_s1=compliance,
            article_p=purpose,
            article_h=hiddenness,
        )

    if dashboard.system_survivability_score < SURVIVABILITY_BLOCK_THRESHOLD:
        return GovernanceGateDecision(
            allow=False,
            level="block",
            reason=(
                f"System survivability below constitutional minimum 0.60 ({ARTICLE_S_REFERENCE})."
            ),
            article_s1=compliance,
            article_p=purpose,
            article_h=hiddenness,
        )

    if dashboard.steward_independence_score < STEWARD_INDEPENDENCE_BLOCK_THRESHOLD:
        return GovernanceGateDecision(
            allow=False,
            level="block",
            reason=(
                f"Steward independence below constitutional minimum 0.60 ({ARTICLE_S_REFERENCE})."
            ),
            article_s1=compliance,
            article_p=purpose,
            article_h=hiddenness,
        )

    if dashboard.founder_dependency_index > FOUNDER_DEPENDENCY_BLOCK_THRESHOLD:
        return GovernanceGateDecision(
            allow=False,
            level="block",
            reason=(
                f"Founder dependency above constitutional maximum 0.40 ({ARTICLE_S_REFERENCE})."
            ),
            article_s1=compliance,
            article_p=purpose,
            article_h=hiddenness,
        )

    if compliance.constitutional_breach:
        return GovernanceGateDecision(
            allow=False,
            level="block",
            reason=f"Survivability threshold table in red zone ({ARTICLE_S_REFERENCE}).",
            article_s1=compliance,
            article_p=purpose,
            article_h=hiddenness,
        )

    degraded = (
        dashboard.system_survivability_score < SURVIVABILITY_WARN_THRESHOLD
        or dashboard.steward_independence_score < STEWARD_INDEPENDENCE_WARN_THRESHOLD
        or dashboard.founder_dependency_index > FOUNDER_DEPENDENCY_WARN_THRESHOLD
        or purpose.purpose_red_zone
        or hiddenness.hidden_red_zone
    )
    if degraded:
        return GovernanceGateDecision(
            allow=True,
            level="warn",
            reason=(
                "Survivability, purpose continuity, or hiddenness in yellow zone; "
                "proceed with explicit awareness."
            ),
            article_s1=compliance,
            article_p=purpose,
            article_h=hiddenness,
        )

    return GovernanceGateDecision(
        allow=True,
        level="ok",
        reason="Survivability, purpose continuity, and hiddenness within green zone.",
        article_s1=compliance,
        article_p=purpose,
        article_h=hiddenness,
    )


def persist_dashboard_governance_decision(
    csr: ConstitutionalStateRuntime,
    decision: GovernanceGateDecision,
) -> GovernanceGateDecision:
    csr.put_domain_doc(DASHBOARD_GOVERNANCE_STATE_ID, "dashboard_governance_gate", decision)
    return decision


def apply_and_persist_dashboard_governance(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
) -> GovernanceGateDecision:
    article_p = load_compliance_from_csr(csr, dashboard)
    article_h = load_article_h_compliance_from_csr(csr, dashboard)
    decision = apply_dashboard_to_governance_gate(
        dashboard,
        article_p=article_p,
        article_h=article_h,
    )
    return persist_dashboard_governance_decision(csr, decision)


def load_dashboard_governance_decision(
    csr: ConstitutionalStateRuntime,
) -> GovernanceGateDecision | None:
    try:
        doc = csr.get_domain_doc(DASHBOARD_GOVERNANCE_STATE_ID, GovernanceGateDecision)
        assert isinstance(doc, GovernanceGateDecision)
        return doc
    except KeyError:
        return None


def apply_dashboard_to_mission_preconditions(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
) -> ReconstructabilityDashboardState:
    """v0: mission gate reads the latest dashboard snapshot from CSR."""
    csr.put_domain_doc(DASHBOARD_STATE_ID, "reconstructability_dashboard", dashboard)
    return dashboard
