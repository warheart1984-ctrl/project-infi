"""Hiddenness Remediation Amendment — UGR-AMENDMENT-H-HIDDENNESS-v0."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_H_REFERENCE,
    ARTICLE_P_REFERENCE,
    ARTICLE_R_REFERENCE,
    ARTICLE_S_REFERENCE,
    HIDDENNESS_AMENDMENT_COMPLETE_INDEX,
    HIDDENNESS_AMENDMENT_TEMPLATE_ID,
    HIDDENNESS_INDEX_THRESHOLD,
    RED_ZONE_HF_THREAT_COUNT,
)
from constitutional.hiddenness.hiddenness_failures import HiddennessFailureClass as HF
from constitutional.hiddenness.hiddenness_runtime import HiddennessState
from constitutional.runtime.runtime import ConstitutionalStateRuntime

HIDDENNESS_AMENDMENT_TRIGGERS_STATE_ID = "hiddenness_amendment_triggers__pending"


class HiddennessAmendmentProposal(BaseModel):
    state_id: str
    state_type: str = "hiddenness_amendment_proposal"
    proposal: dict[str, Any] = Field(default_factory=dict)


class HiddennessAmendmentTriggerRecord(BaseModel):
    scope: str
    reason: str
    threats: list[HF] = Field(default_factory=list)
    opened_at: datetime
    template_id: str = HIDDENNESS_AMENDMENT_TEMPLATE_ID
    escalated: bool = False
    escalation_count: int = Field(default=1, ge=1)


class HiddennessAmendmentTriggersState(BaseModel):
    state_id: str = HIDDENNESS_AMENDMENT_TRIGGERS_STATE_ID
    state_type: str = "hiddenness_amendment_triggers"
    triggers: list[HiddennessAmendmentTriggerRecord] = Field(default_factory=list)


HIDDENNESS_AMENDMENT_TEMPLATE: dict[str, Any] = {
    "template_id": HIDDENNESS_AMENDMENT_TEMPLATE_ID,
    "amendment_type": "HIDDENNESS REMEDIATION AMENDMENT",
    "triggered_by": [
        f"Hiddenness Index < {HIDDENNESS_INDEX_THRESHOLD}",
        f"Any H-F threat in red zone (≥ {RED_ZONE_HF_THREAT_COUNT} failed surfaces)",
        "Any undocumented invariant",
        "Any undocumented purpose fragment",
        "Any implicit authority",
        "Any founder-only knowledge detected",
    ],
    "problem_statement": (
        "The system is in violation of Article H — Hiddenness Doctrine. "
        "Critical knowledge, invariants, purpose fragments, or authority remain implicit or undocumented."
    ),
    "evidence_fields": [
        "Hiddenness State",
        "Hiddenness Index",
        "Failed H-F surfaces",
        "Implicit assumptions",
        "Undocumented invariants",
        "Undocumented purpose fragments",
        "Undocumented authority",
        "Missing cultural context",
        "Missing constraints",
        "Founder-only knowledge",
    ],
    "required_remediation_actions": [
        "Assumption Externalization — convert implicit assumptions into explicit receipts",
        "Invariant Documentation — write missing invariants and add invariant rationale receipts",
        "Purpose Fragment Documentation — document missing purpose components; add purpose continuity receipts",
        "Authority Clarification — make implicit authority explicit; remove founder-exclusive authority",
        "Context Restoration — document cultural/philosophical context; add context receipts",
        "Constraint Encoding — encode undocumented constraints into the constitution",
    ],
    "success_criteria": [
        f"Hiddenness Index ≥ {HIDDENNESS_AMENDMENT_COMPLETE_INDEX}",
        "No H-F threats in red zone",
        "All assumptions externalized",
        "All invariants documented",
        "All purpose fragments documented",
        "All authority explicit",
        "All context documented",
        "Hiddenness Runtime passes",
    ],
    "constitutional_linkage": [
        ARTICLE_H_REFERENCE,
        ARTICLE_P_REFERENCE,
        ARTICLE_S_REFERENCE,
        ARTICLE_R_REFERENCE,
    ],
    "telic_statement": (
        "A system is legitimate only when nothing required for its continuity, "
        "meaning, or evolution remains hidden."
    ),
}


def build_hiddenness_amendment_proposal(hiddenness: HiddennessState) -> dict[str, Any]:
    return {
        **HIDDENNESS_AMENDMENT_TEMPLATE,
        "snapshot_at": hiddenness.snapshot_at.isoformat(),
        "evidence": {
            "hiddenness_state_id": hiddenness.state_id,
            "hiddenness_index": hiddenness.hiddenness_index,
            "failed_surfaces": [hf.value for hf in hiddenness.failed_surfaces],
            "implicit_assumptions": list(hiddenness.implicit_assumptions),
            "undocumented_invariants": list(hiddenness.undocumented_invariants),
            "undocumented_purpose_fragments": list(hiddenness.undocumented_purpose_fragments),
            "undocumented_authority": list(hiddenness.undocumented_authority),
            "undocumented_context": list(hiddenness.undocumented_context),
            "undocumented_constraints": list(hiddenness.undocumented_constraints),
            "founder_only_knowledge": list(hiddenness.founder_only_knowledge),
            "missing_items": list(hiddenness.missing_items),
        },
    }


def should_trigger_hiddenness_amendment(hiddenness: HiddennessState) -> bool:
    if hiddenness.hiddenness_index < HIDDENNESS_INDEX_THRESHOLD:
        return True
    if len(hiddenness.failed_surfaces) >= RED_ZONE_HF_THREAT_COUNT:
        return True
    if hiddenness.undocumented_invariants:
        return True
    if hiddenness.undocumented_purpose_fragments:
        return True
    if hiddenness.undocumented_authority:
        return True
    if hiddenness.implicit_assumptions:
        return True
    if hiddenness.founder_only_knowledge:
        return True
    return bool(hiddenness.failed_surfaces)


def load_hiddenness_amendment_triggers(
    csr: ConstitutionalStateRuntime,
) -> HiddennessAmendmentTriggersState:
    try:
        doc = csr.get_domain_doc(HIDDENNESS_AMENDMENT_TRIGGERS_STATE_ID, HiddennessAmendmentTriggersState)
        assert isinstance(doc, HiddennessAmendmentTriggersState)
        return doc
    except KeyError:
        return HiddennessAmendmentTriggersState()


def save_hiddenness_amendment_triggers(
    csr: ConstitutionalStateRuntime,
    state: HiddennessAmendmentTriggersState,
) -> None:
    csr.put_domain_doc(HIDDENNESS_AMENDMENT_TRIGGERS_STATE_ID, "hiddenness_amendment_triggers", state)


def open_or_escalate_hiddenness_amendment(
    csr: ConstitutionalStateRuntime,
    *,
    scope: str,
    reason: str,
    threats: list[HF],
    opened_at: datetime | None = None,
) -> HiddennessAmendmentTriggerRecord:
    now = opened_at or datetime.now(UTC).replace(microsecond=0)
    state = load_hiddenness_amendment_triggers(csr)
    for record in state.triggers:
        if record.scope == scope:
            record.escalated = True
            record.escalation_count += 1
            merged = set(record.threats)
            merged.update(threats)
            record.threats = list(merged)
            save_hiddenness_amendment_triggers(csr, state)
            return record

    record = HiddennessAmendmentTriggerRecord(
        scope=scope,
        reason=reason,
        threats=list(dict.fromkeys(threats)),
        opened_at=now,
    )
    state.triggers.append(record)
    save_hiddenness_amendment_triggers(csr, state)
    return record


def maybe_trigger_hiddenness_amendment(
    csr: ConstitutionalStateRuntime,
    hiddenness: HiddennessState,
    *,
    opened_at: datetime | None = None,
) -> list[HiddennessAmendmentTriggerRecord]:
    if not should_trigger_hiddenness_amendment(hiddenness):
        return []

    proposal = build_hiddenness_amendment_proposal(hiddenness)
    csr.put_domain_doc(
        f"hiddenness_amendment_proposal__{hiddenness.version}",
        "hiddenness_amendment_proposal",
        HiddennessAmendmentProposal(
            state_id=f"hiddenness_amendment_proposal__{hiddenness.version}",
            proposal=proposal,
        ),
    )

    return [
        open_or_escalate_hiddenness_amendment(
            csr,
            scope="hiddenness",
            reason=HIDDENNESS_AMENDMENT_TEMPLATE["problem_statement"],
            threats=list(hiddenness.failed_surfaces),
            opened_at=opened_at,
        )
    ]
