"""Article H hiddenness governance — gates high-impact actions when knowledge is implicit."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_H_REFERENCE,
    HIDDENNESS_INDEX_THRESHOLD,
    RED_ZONE_HF_THREAT_COUNT,
    SUCCESSION_MIN_HIDDENNESS_INDEX,
)
from constitutional.hiddenness.hiddenness_failures import HiddennessFailureClass as HF
from constitutional.hiddenness.hiddenness_runtime import HiddennessState, load_hiddenness_state
from constitutional.runtime.reconstructability_dashboard import ReconstructabilityDashboardState
from constitutional.runtime.runtime import ConstitutionalStateRuntime


class ArticleHCompliance(BaseModel):
    hiddenness_index: float = Field(ge=0.0, le=1.0)
    hidden_threat_count: int = Field(ge=0)
    hidden_red_zone: bool = False
    implicit_assumption_count: int = Field(default=0, ge=0)
    undocumented_invariant_count: int = Field(default=0, ge=0)
    undocumented_purpose_fragment_count: int = Field(default=0, ge=0)
    undocumented_authority_count: int = Field(default=0, ge=0)
    undocumented_constraint_count: int = Field(default=0, ge=0)
    founder_only_knowledge_count: int = Field(default=0, ge=0)
    constitutional_breach: bool = False
    block_reasons: list[str] = Field(default_factory=list)


def hiddenness_in_red_zone(hidden_threats: list[HF]) -> bool:
    return len(hidden_threats) >= RED_ZONE_HF_THREAT_COUNT


def hiddenness_runtime_passes(
    hiddenness: HiddennessState | None,
    *,
    min_index: float = HIDDENNESS_INDEX_THRESHOLD,
) -> bool:
    if hiddenness is None:
        return False
    return hiddenness.hiddenness_index >= min_index and len(hiddenness.failed_surfaces) == 0


def evaluate_article_h_compliance(
    dashboard: ReconstructabilityDashboardState,
    *,
    hiddenness: HiddennessState | None = None,
) -> ArticleHCompliance:
    index = dashboard.hiddenness_index
    threats = list(dashboard.hidden_threats)
    red_zone = hiddenness_in_red_zone(threats)

    assumptions = list(dashboard.implicit_assumptions)
    invariants = list(dashboard.undocumented_invariants)
    purpose_fragments = list(dashboard.undocumented_purpose_fragments)
    authority = list(dashboard.undocumented_authority)
    constraints = list(dashboard.undocumented_constraints)
    founder_only = list(dashboard.founder_only_knowledge)

    if hiddenness is not None:
        index = hiddenness.hiddenness_index
        threats = list(hiddenness.failed_surfaces)
        red_zone = hiddenness_in_red_zone(threats)
        assumptions = list(hiddenness.implicit_assumptions)
        invariants = list(hiddenness.undocumented_invariants)
        purpose_fragments = list(hiddenness.undocumented_purpose_fragments)
        authority = list(hiddenness.undocumented_authority)
        constraints = list(hiddenness.undocumented_constraints)
        founder_only = list(hiddenness.founder_only_knowledge)

    block_reasons: list[str] = []
    if index < HIDDENNESS_INDEX_THRESHOLD:
        block_reasons.append("hiddenness_index_below_threshold")
    if red_zone:
        block_reasons.append("hidden_threats_in_red_zone")
    if assumptions:
        block_reasons.append("implicit_assumptions_exist")
    if invariants:
        block_reasons.append("undocumented_invariants_exist")
    if purpose_fragments:
        block_reasons.append("undocumented_purpose_fragments_exist")
    if authority:
        block_reasons.append("implicit_authority_exists")
    if constraints:
        block_reasons.append("undocumented_constraints_exist")
    if founder_only:
        block_reasons.append("founder_only_knowledge_exists")

    if hiddenness is not None:
        drift = getattr(hiddenness, "invariant_drift_candidates", None) or []
        mismatches = getattr(hiddenness, "semantic_mismatches", None) or []
        lineage_gaps = getattr(hiddenness, "lineage_gaps", None) or []
        if drift:
            block_reasons.append("invariant_drift_detected")
        if mismatches:
            block_reasons.append("semantic_mismatch_detected")
        if lineage_gaps:
            block_reasons.append("lineage_gaps_detected")

    return ArticleHCompliance(
        hiddenness_index=index,
        hidden_threat_count=len(threats),
        hidden_red_zone=red_zone,
        implicit_assumption_count=len(assumptions),
        undocumented_invariant_count=len(invariants),
        undocumented_purpose_fragment_count=len(purpose_fragments),
        undocumented_authority_count=len(authority),
        undocumented_constraint_count=len(constraints),
        founder_only_knowledge_count=len(founder_only),
        constitutional_breach=bool(block_reasons),
        block_reasons=block_reasons,
    )


def succession_hiddenness_ready(
    dashboard: ReconstructabilityDashboardState,
    *,
    hiddenness: HiddennessState | None = None,
) -> tuple[bool, list[str]]:
    """Article H succession gates — index ≥ 0.80 and no hidden continuity knowledge."""
    compliance = evaluate_article_h_compliance(dashboard, hiddenness=hiddenness)
    reasons: list[str] = []

    if compliance.hiddenness_index < SUCCESSION_MIN_HIDDENNESS_INDEX:
        reasons.append("hiddenness_index_below_succession_threshold")
    if compliance.hidden_red_zone:
        reasons.append("hidden_threats_in_red_zone")
    if compliance.implicit_assumption_count > 0:
        reasons.append("implicit_assumptions_exist")
    if compliance.undocumented_invariant_count > 0:
        reasons.append("undocumented_invariants_exist")
    if compliance.undocumented_purpose_fragment_count > 0:
        reasons.append("undocumented_purpose_fragments_exist")
    if compliance.undocumented_authority_count > 0:
        reasons.append("implicit_authority_exists")
    if compliance.undocumented_constraint_count > 0:
        reasons.append("undocumented_constraints_exist")
    if compliance.founder_only_knowledge_count > 0:
        reasons.append("founder_only_knowledge_exists")
    if not hiddenness_runtime_passes(
        hiddenness,
        min_index=SUCCESSION_MIN_HIDDENNESS_INDEX,
    ):
        if hiddenness is None:
            reasons.append("hiddenness_scan_never_run")
        else:
            reasons.append("hiddenness_runtime_failed")

    return len(reasons) == 0, reasons


def load_article_h_compliance_from_csr(csr, dashboard: ReconstructabilityDashboardState) -> ArticleHCompliance:
    hiddenness = load_hiddenness_for_governance(csr)
    return evaluate_article_h_compliance(dashboard, hiddenness=hiddenness)


def load_hiddenness_for_governance(csr: ConstitutionalStateRuntime) -> HiddennessState | None:
    try:
        from constitutional.hiddenness.hiddenness_runtime_v2 import (
            HiddennessStateV2,
            load_hiddenness_state_v2,
        )

        return load_hiddenness_state_v2(csr)
    except KeyError:
        try:
            return load_hiddenness_state(csr)
        except KeyError:
            return None


def apply_hiddenness_to_governance_gate(
    hiddenness: HiddennessState,
) -> GovernanceGateDecision | None:
    """Article H gate from hiddenness runtime output — blocks on index and critical surfaces."""
    from constitutional.runtime.dashboard_governance import GovernanceGateDecision

    if hiddenness.hiddenness_index < HIDDENNESS_INDEX_THRESHOLD:
        return GovernanceGateDecision(
            allow=False,
            level="block",
            reason=(
                f"Hiddenness above constitutional threshold ({ARTICLE_H_REFERENCE}): "
                f"index={hiddenness.hiddenness_index:.2f}."
            ),
        )

    critical = {
        HF.HIDDEN_INVARIANT,
        HF.HIDDEN_PURPOSE_FRAGMENT,
        HF.HIDDEN_AUTHORITY,
    }
    if any(surface in hiddenness.failed_surfaces for surface in critical):
        codes = ", ".join(surface.value.split()[0] for surface in hiddenness.failed_surfaces if surface in critical)
        return GovernanceGateDecision(
            allow=False,
            level="block",
            reason=f"Critical hiddenness detected (invariant/purpose/authority): {codes}.",
        )

    return GovernanceGateDecision(
        allow=True,
        level="ok",
        reason="Hiddenness within acceptable bounds.",
    )


def apply_hiddenness_to_amendment_triggers(
    csr: ConstitutionalStateRuntime,
    hiddenness: HiddennessState,
    *,
    opened_at: datetime | None = None,
) -> list:
    """Escalate hiddenness remediation when runtime detects implicit critical elements."""
    from datetime import UTC, datetime

    from constitutional.hiddenness.hiddenness_amendment import maybe_trigger_hiddenness_amendment

    if hiddenness.hiddenness_index >= HIDDENNESS_INDEX_THRESHOLD and not hiddenness.failed_surfaces:
        return []
    return maybe_trigger_hiddenness_amendment(
        csr,
        hiddenness,
        opened_at=opened_at or datetime.now(UTC).replace(microsecond=0),
    )
