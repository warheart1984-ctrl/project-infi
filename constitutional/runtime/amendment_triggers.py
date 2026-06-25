"""Amendment triggers — escalate structural change when reconstructability keeps failing."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_S2_REFERENCE,
    ARTICLE_S_REFERENCE,
    FOUNDER_DEPENDENCY_BLOCK_THRESHOLD,
    FOUNDER_DEPENDENCY_MANDATORY_SUCCESSION_THRESHOLD,
    MANDATORY_SUCCESSION_CYCLES,
    SURVIVABILITY_BLOCK_THRESHOLD,
)
from constitutional.runtime.reconstructability_dashboard import ReconstructabilityDashboardState
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessState
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.survivability_amendment import open_or_escalate_survivability_amendment

AMENDMENT_TRIGGERS_STATE_ID = "amendment_triggers__pending"


class AmendmentTriggerRecord(BaseModel):
    scope: str
    reason: str
    threats: list[RF] = Field(default_factory=list)
    opened_at: datetime
    escalated: bool = False
    escalation_count: int = Field(default=1, ge=1)


class AmendmentTriggersState(BaseModel):
    state_id: str = AMENDMENT_TRIGGERS_STATE_ID
    state_type: str = "amendment_triggers"
    triggers: list[AmendmentTriggerRecord] = Field(default_factory=list)


def load_amendment_triggers(csr: ConstitutionalStateRuntime) -> AmendmentTriggersState:
    try:
        doc = csr.get_domain_doc(AMENDMENT_TRIGGERS_STATE_ID, AmendmentTriggersState)
        assert isinstance(doc, AmendmentTriggersState)
        return doc
    except KeyError:
        return AmendmentTriggersState()


def save_amendment_triggers(csr: ConstitutionalStateRuntime, state: AmendmentTriggersState) -> None:
    csr.put_domain_doc(AMENDMENT_TRIGGERS_STATE_ID, "amendment_triggers", state)


def open_or_escalate_amendment(
    csr: ConstitutionalStateRuntime,
    *,
    scope: str,
    reason: str,
    threats: list[RF],
    opened_at: datetime | None = None,
) -> AmendmentTriggerRecord:
    now = opened_at or datetime.now(UTC).replace(microsecond=0)
    state = load_amendment_triggers(csr)
    for record in state.triggers:
        if record.scope == scope:
            record.escalated = True
            record.escalation_count += 1
            merged = set(record.threats)
            merged.update(threats)
            record.threats = list(merged)
            save_amendment_triggers(csr, state)
            return record

    record = AmendmentTriggerRecord(
        scope=scope,
        reason=reason,
        threats=list(dict.fromkeys(threats)),
        opened_at=now,
    )
    state.triggers.append(record)
    save_amendment_triggers(csr, state)
    return record


def maybe_trigger_reconstructability_amendment(
    csr: ConstitutionalStateRuntime,
    rf_state: ReconstructabilityFitnessState,
    *,
    opened_at: datetime | None = None,
) -> list[AmendmentTriggerRecord]:
    """Open or escalate amendments when persistent fitness failures demand structural change."""
    opened: list[AmendmentTriggerRecord] = []
    persistent = rf_state.failed_surfaces

    if RF.STEWARD_DISCONTINUITY in persistent:
        opened.append(
            open_or_escalate_amendment(
                csr,
                scope="stewardship",
                reason="Repeated failure of cold-start steward test",
                threats=[RF.STEWARD_DISCONTINUITY],
                opened_at=opened_at,
            )
        )

    if RF.EVIDENCE_LOSS in persistent or RF.LINEAGE_BREAK in persistent:
        opened.append(
            open_or_escalate_amendment(
                csr,
                scope="ledger_and_receipts",
                reason="Repeated failure of evidence/lineage reconstructability",
                threats=[RF.EVIDENCE_LOSS, RF.LINEAGE_BREAK],
                opened_at=opened_at,
            )
        )

    return opened


def apply_dashboard_to_amendment_triggers(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
    *,
    fitness: ReconstructabilityFitnessState | None = None,
    opened_at: datetime | None = None,
    mandatory_founder_cycles: int = 0,
) -> list[AmendmentTriggerRecord]:
    """Open or escalate amendments when Article S / S-2 survivability thresholds are breached."""
    opened: list[AmendmentTriggerRecord] = []

    survivability_amendment = open_or_escalate_survivability_amendment(
        csr, dashboard, fitness=fitness, opened_at=opened_at
    )
    if survivability_amendment is not None:
        opened.append(
            open_or_escalate_amendment(
                csr,
                scope="survivability_remediation",
                reason=survivability_amendment.reason,
                threats=list(dashboard.active_threats),
                opened_at=opened_at,
            )
        )

    if dashboard.system_survivability_score < SURVIVABILITY_BLOCK_THRESHOLD:
        opened.append(
            open_or_escalate_amendment(
                csr,
                scope="survivability",
                reason=f"System survivability below constitutional threshold ({ARTICLE_S_REFERENCE}).",
                threats=list(dashboard.active_threats),
                opened_at=opened_at,
            )
        )

    if dashboard.founder_dependency_index > FOUNDER_DEPENDENCY_BLOCK_THRESHOLD:
        opened.append(
            open_or_escalate_amendment(
                csr,
                scope="stewardship",
                reason=f"Founder dependency violates {ARTICLE_S_REFERENCE}.",
                threats=[RF.STEWARD_DISCONTINUITY],
                opened_at=opened_at,
            )
        )

    if (
        dashboard.founder_dependency_index > FOUNDER_DEPENDENCY_MANDATORY_SUCCESSION_THRESHOLD
        and mandatory_founder_cycles >= MANDATORY_SUCCESSION_CYCLES
    ):
        opened.append(
            open_or_escalate_amendment(
                csr,
                scope="succession_readiness",
                reason=(
                    f"Founder dependency above {FOUNDER_DEPENDENCY_MANDATORY_SUCCESSION_THRESHOLD} "
                    f"for {MANDATORY_SUCCESSION_CYCLES}+ cycles ({ARTICLE_S2_REFERENCE})."
                ),
                threats=[RF.STEWARD_DISCONTINUITY],
                opened_at=opened_at,
            )
        )

    threats = set(dashboard.active_threats)
    if RF.EVIDENCE_LOSS in threats or RF.LINEAGE_BREAK in threats:
        opened.append(
            open_or_escalate_amendment(
                csr,
                scope="ledger_and_receipts",
                reason="Persistent evidence/lineage reconstructability failures",
                threats=[RF.EVIDENCE_LOSS, RF.LINEAGE_BREAK],
                opened_at=opened_at,
            )
        )

    return opened
