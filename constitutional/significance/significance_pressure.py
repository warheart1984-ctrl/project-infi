"""Significance pressure — amendments and reclassification from Q-F failures."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.core.articles import (
    SIGNIFICANCE_AMENDMENT_TEMPLATE_ID,
    SIGNIFICANCE_HEALTH_THRESHOLD,
    SIGNIFICANCE_STABILITY_AMENDMENT_TEMPLATE_ID,
    SIGNIFICANCE_STABILITY_THRESHOLD,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.significance_failures import SignificanceFailureClass as QF
from constitutional.significance.significance_runtime import SignificanceAuditState
from constitutional.significance.significance_stability_runtime import SignificanceStabilityState


SIGNIFICANCE_AMENDMENT_TRIGGERS_STATE_ID = "significance_amendment_triggers__pending"


class SignificanceAmendmentTriggerRecord:
    def __init__(self, scope: str, reason: str, template_id: str, opened_at: datetime) -> None:
        self.scope = scope
        self.reason = reason
        self.template_id = template_id
        self.opened_at = opened_at


def open_or_escalate_significance_amendment(
    csr: ConstitutionalStateRuntime,
    *,
    scope: str,
    reason: str,
    template_id: str = SIGNIFICANCE_AMENDMENT_TEMPLATE_ID,
    opened_at: datetime | None = None,
) -> SignificanceAmendmentTriggerRecord:
    now = opened_at or datetime.now(UTC).replace(microsecond=0)
    from pydantic import BaseModel, Field

    class SignificanceAmendmentTriggersState(BaseModel):
        state_id: str = SIGNIFICANCE_AMENDMENT_TRIGGERS_STATE_ID
        state_type: str = "significance_amendment_triggers"
        triggers: list[dict[str, str]] = Field(default_factory=list)

    try:
        state = csr.get_domain_doc(SIGNIFICANCE_AMENDMENT_TRIGGERS_STATE_ID, SignificanceAmendmentTriggersState)
    except KeyError:
        state = SignificanceAmendmentTriggersState()

    record = {
        "scope": scope,
        "reason": reason,
        "template_id": template_id,
        "opened_at": now.isoformat(),
    }
    state.triggers.append(record)
    csr.put_domain_doc(SIGNIFICANCE_AMENDMENT_TRIGGERS_STATE_ID, "significance_amendment_triggers", state)
    return SignificanceAmendmentTriggerRecord(scope, reason, template_id, now)


def apply_significance_pressure(
    csr: ConstitutionalStateRuntime,
    significance: SignificanceAuditState,
    stability: SignificanceStabilityState | None = None,
    *,
    opened_at: datetime | None = None,
) -> None:
    """Drive significance amendments from Q-F failures."""
    now = opened_at or datetime.now(UTC).replace(microsecond=0)

    if significance.significance_health_index < SIGNIFICANCE_HEALTH_THRESHOLD or significance.failed_surfaces:
        open_or_escalate_significance_amendment(
            csr,
            scope="significance",
            reason="Significance health below constitutional threshold.",
            opened_at=now,
        )

    if QF.TIER_BLOAT in significance.failed_surfaces:
        open_or_escalate_significance_amendment(
            csr,
            scope="tier_bloat",
            reason="Tier 0/1 bloat detected — block amendments that expand core tiers.",
            opened_at=now,
        )

    if significance.suspected_misranked_artifacts:
        open_or_escalate_significance_amendment(
            csr,
            scope="reclassification",
            reason="Mis-ranked core artifacts require reclassification.",
            opened_at=now,
        )

    if stability is not None and (
        stability.stability_index < SIGNIFICANCE_STABILITY_THRESHOLD
        or QF.SIGNIFICANCE_DRIFT in stability.failed_surfaces
    ):
        open_or_escalate_significance_amendment(
            csr,
            scope="significance_stability",
            reason="Significance drift detected without constitutional justification.",
            template_id=SIGNIFICANCE_STABILITY_AMENDMENT_TEMPLATE_ID,
            opened_at=now,
        )
