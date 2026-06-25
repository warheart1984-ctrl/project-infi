"""Purpose continuity — P-F threats, mission fidelity, and amendment templates."""

from constitutional.purpose.purpose_continuity_amendment import (
    PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE,
    PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID,
    PurposeAmendmentTriggerRecord,
    PurposeAmendmentTriggersState,
    build_purpose_continuity_amendment_proposal,
    maybe_trigger_purpose_continuity_amendment,
    open_or_escalate_purpose_amendment,
    should_trigger_purpose_continuity_amendment,
)

__all__ = [
    "PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE",
    "PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID",
    "PurposeAmendmentTriggerRecord",
    "PurposeAmendmentTriggersState",
    "build_purpose_continuity_amendment_proposal",
    "maybe_trigger_purpose_continuity_amendment",
    "open_or_escalate_purpose_amendment",
    "should_trigger_purpose_continuity_amendment",
]
