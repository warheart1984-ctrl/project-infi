"""Purpose Continuity Amendment — UGR-AMENDMENT-P-PURPOSE-CONTINUITY-v0."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_P_REFERENCE,
    ARTICLE_R_REFERENCE,
    ARTICLE_S_REFERENCE,
    INVARIANT_INTERPRETATION_MIN_SCORE,
    INVARIANT_INTERPRETATION_SUCCESS_SCORE,
    MISSION_LEGIBILITY_MIN_SCORE,
    PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID,
    PURPOSE_CONTINUITY_INDEX_THRESHOLD,
)
from constitutional.runtime.mission_fidelity_runtime import MissionFidelityState
from constitutional.runtime.purpose_failures import PurposeFailureClass as PF
from constitutional.runtime.runtime import ConstitutionalStateRuntime

PURPOSE_AMENDMENT_TRIGGERS_STATE_ID = "purpose_amendment_triggers__pending"


class PurposeContinuityAmendmentProposal(BaseModel):
    state_id: str
    state_type: str = "purpose_continuity_amendment_proposal"
    proposal: dict[str, Any] = Field(default_factory=dict)


class PurposeAmendmentTriggerRecord(BaseModel):
    scope: str
    reason: str
    threats: list[PF] = Field(default_factory=list)
    opened_at: datetime
    template_id: str = PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID
    escalated: bool = False
    escalation_count: int = Field(default=1, ge=1)


class PurposeAmendmentTriggersState(BaseModel):
    state_id: str = PURPOSE_AMENDMENT_TRIGGERS_STATE_ID
    state_type: str = "purpose_amendment_triggers"
    triggers: list[PurposeAmendmentTriggerRecord] = Field(default_factory=list)


PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE: dict[str, Any] = {
    "template_id": PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID,
    "amendment_type": "PURPOSE CONTINUITY REMEDIATION AMENDMENT",
    "triggered_by": [
        f"Purpose Continuity Index < {PURPOSE_CONTINUITY_INDEX_THRESHOLD}",
        f"Mission Legibility Score < {MISSION_LEGIBILITY_MIN_SCORE}",
        f"Invariant Interpretation Score < {INVARIANT_INTERPRETATION_MIN_SCORE}",
        "Any P-F threat in red zone (failed surface)",
    ],
    "problem_statement": (
        "The system is in violation of Article P — Purpose Continuity Doctrine. "
        "The founding purpose is at risk of dilution, drift, or misinterpretation."
    ),
    "evidence_fields": [
        "Mission Fidelity State",
        "Purpose Continuity Index",
        "Failed P-F surfaces",
        "Missing purpose artifacts",
        "Ambiguous invariant interpretations",
        "Conflicting purpose justifications",
    ],
    "required_remediation_actions": [
        "Mission Re-Legibility (rewrite mission statement, add purpose receipts, clarify invariant rationale)",
        "Invariant Re-Interpretation (interpretation receipts, resolve ambiguous interpretations)",
        "Purpose Drift Correction (identify drift vectors, realign runtimes and policies)",
        "Purpose Fragmentation Repair (unify conflicting interpretations, reconcile subsystem purposes)",
        "Cultural Context Restoration (restore philosophical grounding, re-embed founding context)",
    ],
    "success_criteria": [
        f"Purpose Continuity Index ≥ {PURPOSE_CONTINUITY_INDEX_THRESHOLD}",
        f"Mission Legibility Score = {MISSION_LEGIBILITY_MIN_SCORE}",
        f"Invariant Interpretation Score ≥ {INVARIANT_INTERPRETATION_SUCCESS_SCORE}",
        "No P-F threats in red zone",
        "Mission Fidelity Test passes",
    ],
    "constitutional_linkage": [
        ARTICLE_P_REFERENCE,
        ARTICLE_S_REFERENCE,
        ARTICLE_R_REFERENCE,
    ],
    "telic_statement": (
        "A system is legitimate only if it preserves the meaning it was created to protect."
    ),
}


def build_purpose_continuity_amendment_proposal(
    mf_state: MissionFidelityState,
) -> dict[str, Any]:
    """Materialize template with live Mission Fidelity evidence."""
    return {
        **PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE,
        "snapshot_at": mf_state.snapshot_at.isoformat(),
        "evidence": {
            "mission_fidelity_state_id": mf_state.state_id,
            "purpose_continuity_index": mf_state.purpose_continuity_index,
            "purpose_fidelity_score": mf_state.purpose_fidelity_score,
            "invariant_interpretation_score": mf_state.invariant_interpretation_score,
            "mission_legibility_score": mf_state.mission_legibility_score,
            "failed_surfaces": [pf.value for pf in mf_state.failed_surfaces],
            "missing_purpose_artifacts": list(mf_state.missing_purpose_artifacts),
            "ambiguous_interpretations": list(mf_state.ambiguous_interpretations),
            "conflicting_justifications": list(mf_state.conflicting_justifications),
        },
    }


def should_trigger_purpose_continuity_amendment(mf_state: MissionFidelityState) -> bool:
    if mf_state.purpose_continuity_index < PURPOSE_CONTINUITY_INDEX_THRESHOLD:
        return True
    if mf_state.mission_legibility_score < MISSION_LEGIBILITY_MIN_SCORE:
        return True
    if mf_state.invariant_interpretation_score < INVARIANT_INTERPRETATION_MIN_SCORE:
        return True
    return bool(mf_state.failed_surfaces)


def load_purpose_amendment_triggers(csr: ConstitutionalStateRuntime) -> PurposeAmendmentTriggersState:
    try:
        doc = csr.get_domain_doc(PURPOSE_AMENDMENT_TRIGGERS_STATE_ID, PurposeAmendmentTriggersState)
        assert isinstance(doc, PurposeAmendmentTriggersState)
        return doc
    except KeyError:
        return PurposeAmendmentTriggersState()


def save_purpose_amendment_triggers(
    csr: ConstitutionalStateRuntime,
    state: PurposeAmendmentTriggersState,
) -> None:
    csr.put_domain_doc(PURPOSE_AMENDMENT_TRIGGERS_STATE_ID, "purpose_amendment_triggers", state)


def open_or_escalate_purpose_amendment(
    csr: ConstitutionalStateRuntime,
    *,
    scope: str,
    reason: str,
    threats: list[PF],
    opened_at: datetime | None = None,
) -> PurposeAmendmentTriggerRecord:
    now = opened_at or datetime.now(UTC).replace(microsecond=0)
    state = load_purpose_amendment_triggers(csr)
    for record in state.triggers:
        if record.scope == scope:
            record.escalated = True
            record.escalation_count += 1
            merged = set(record.threats)
            merged.update(threats)
            record.threats = list(merged)
            save_purpose_amendment_triggers(csr, state)
            return record

    record = PurposeAmendmentTriggerRecord(
        scope=scope,
        reason=reason,
        threats=list(dict.fromkeys(threats)),
        opened_at=now,
    )
    state.triggers.append(record)
    save_purpose_amendment_triggers(csr, state)
    return record


def maybe_trigger_purpose_continuity_amendment(
    csr: ConstitutionalStateRuntime,
    mf_state: MissionFidelityState,
    *,
    opened_at: datetime | None = None,
) -> list[PurposeAmendmentTriggerRecord]:
    if not should_trigger_purpose_continuity_amendment(mf_state):
        return []

    proposal = build_purpose_continuity_amendment_proposal(mf_state)
    csr.put_domain_doc(
        f"purpose_amendment_proposal__{mf_state.version}",
        "purpose_continuity_amendment_proposal",
        PurposeContinuityAmendmentProposal(
            state_id=f"purpose_amendment_proposal__{mf_state.version}",
            proposal=proposal,
        ),
    )

    opened: list[PurposeAmendmentTriggerRecord] = []
    opened.append(
        open_or_escalate_purpose_amendment(
            csr,
            scope="purpose_continuity",
            reason=PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE["problem_statement"],
            threats=list(mf_state.failed_surfaces),
            opened_at=opened_at,
        )
    )

    if PF.MISSION_AMNESIA in mf_state.failed_surfaces or PF.PURPOSE_AMBIGUITY in mf_state.failed_surfaces:
        opened.append(
            open_or_escalate_purpose_amendment(
                csr,
                scope="mission_legibility",
                reason="Mission is not legible to future stewards",
                threats=[PF.MISSION_AMNESIA, PF.PURPOSE_AMBIGUITY],
                opened_at=opened_at,
            )
        )

    if PF.INVARIANT_DILUTION in mf_state.failed_surfaces:
        opened.append(
            open_or_escalate_purpose_amendment(
                csr,
                scope="invariant_interpretation",
                reason="Invariant meaning is diluted or ambiguous",
                threats=[PF.INVARIANT_DILUTION],
                opened_at=opened_at,
            )
        )

    return opened
