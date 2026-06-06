"""Earnable reward events and required anchors per event type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Subsystem events
EVENT_SUBSYSTEM_DISCOVERED = "subsystem_discovered"
EVENT_SUBSYSTEM_PROMOTED = "subsystem_promoted"
EVENT_SUBSYSTEM_ADOPTED = "subsystem_adopted"

# Workflow events
EVENT_WORKFLOW_CHAIN_COMPLETED = "workflow_chain_completed"
EVENT_WORKFLOW_LIBRARY_ADMITTED = "workflow_library_admitted"

# Organ events
EVENT_PROVIDER_ORGAN_ADMITTED = "provider_organ_admitted"
EVENT_SUBSYSTEM_ORGAN_PROMOTED = "subsystem_organ_promoted"

# Proof events
EVENT_PROOF_PACKET_PUBLISHED = "proof_packet_published"
EVENT_TRUST_BUNDLE_PASSED = "trust_bundle_passed"

# Invariant events
EVENT_CLOUD_INVARIANT_SET_PASSED = "cloud_invariant_set_passed"

# Capability events
EVENT_CAPABILITY_BRIDGE_EXECUTED = "capability_bridge_executed"
EVENT_CAPABILITY_MODULE_ADMITTED = "capability_module_admitted"

# Substrate events
EVENT_PATTERN_CLAIM_ACCEPTED = "pattern_claim_accepted"
EVENT_SUBSTRATE_ENVELOPE_ATTACHED = "substrate_envelope_attached"

# Transfer / purchase events
EVENT_RAIL_CREDITS_SENT = "rail_credits_sent"
EVENT_RAIL_CREDITS_RECEIVED = "rail_credits_received"
EVENT_RAIL_CREDITS_PURCHASED = "rail_credits_purchased"

DISCOVERY_EVENT_TYPES = frozenset(
    {
        EVENT_SUBSYSTEM_DISCOVERED,
        EVENT_WORKFLOW_CHAIN_COMPLETED,
        EVENT_WORKFLOW_LIBRARY_ADMITTED,
        EVENT_PROVIDER_ORGAN_ADMITTED,
        EVENT_SUBSYSTEM_ORGAN_PROMOTED,
        EVENT_PROOF_PACKET_PUBLISHED,
        EVENT_TRUST_BUNDLE_PASSED,
        EVENT_CLOUD_INVARIANT_SET_PASSED,
        EVENT_CAPABILITY_BRIDGE_EXECUTED,
        EVENT_CAPABILITY_MODULE_ADMITTED,
        EVENT_PATTERN_CLAIM_ACCEPTED,
        EVENT_SUBSTRATE_ENVELOPE_ATTACHED,
    }
)

REWARD_EVENT_TYPES = frozenset(
    {
        *DISCOVERY_EVENT_TYPES,
        EVENT_SUBSYSTEM_PROMOTED,
        EVENT_SUBSYSTEM_ADOPTED,
        EVENT_RAIL_CREDITS_SENT,
        EVENT_RAIL_CREDITS_RECEIVED,
        EVENT_RAIL_CREDITS_PURCHASED,
    }
)

TRANSFER_EVENT_TYPES = frozenset(
    {
        EVENT_RAIL_CREDITS_SENT,
        EVENT_RAIL_CREDITS_RECEIVED,
    }
)

LIFECYCLE_CHAIN = (
    "discovery",
    "proof",
    "receipt",
    "governance",
    "promotion",
    "adoption",
    "attribution",
    "reward",
)

CONTRIBUTION_TYPE_DISCOVERY_EVENTS = {
    "subsystem": EVENT_SUBSYSTEM_DISCOVERED,
    "workflow": EVENT_WORKFLOW_CHAIN_COMPLETED,
    "organ": EVENT_PROVIDER_ORGAN_ADMITTED,
    "proof": EVENT_PROOF_PACKET_PUBLISHED,
    "invariant": EVENT_CLOUD_INVARIANT_SET_PASSED,
    "capability": EVENT_CAPABILITY_BRIDGE_EXECUTED,
    "substrate": EVENT_PATTERN_CLAIM_ACCEPTED,
}


def event_type_for_contribution(contribution_type: str, *, stage: str = "discovered") -> str:
    ctype = str(contribution_type or "subsystem").strip().lower()
    if stage == "discovered":
        return CONTRIBUTION_TYPE_DISCOVERY_EVENTS.get(ctype, EVENT_SUBSYSTEM_DISCOVERED)
    if stage == "promoted" and ctype == "subsystem":
        return EVENT_SUBSYSTEM_PROMOTED
    if stage == "adopted" and ctype == "subsystem":
        return EVENT_SUBSYSTEM_ADOPTED
    return CONTRIBUTION_TYPE_DISCOVERY_EVENTS.get(ctype, EVENT_SUBSYSTEM_DISCOVERED)


@dataclass(frozen=True)
class RewardEventSpec:
    event_type: str
    lifecycle_stage: str
    requires_contribution_id: bool = True
    requires_governance_mission_id: bool = False
    requires_promotion_organ_id: bool = False
    requires_purchase_receipt: bool = False

    def validate_request(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if self.event_type not in REWARD_EVENT_TYPES:
            errors.append(f"unknown event_type: {self.event_type}")
        if self.requires_governance_mission_id and not str(payload.get("governance_mission_id") or "").strip():
            errors.append("governance_mission_id required")
        if self.requires_promotion_organ_id and not str(payload.get("promotion_organ_id") or "").strip():
            errors.append("promotion_organ_id required")
        if self.requires_contribution_id:
            cid = str(payload.get("contribution_id") or payload.get("subsystem_id") or "").strip()
            if not cid:
                errors.append("contribution_id required")
        if not str(payload.get("operator_id") or "").strip():
            errors.append("operator_id required")
        if not str(payload.get("tenant_id") or "").strip():
            errors.append("tenant_id required")
        return errors


def _spec(event_type: str, lifecycle_stage: str = "reward", **kwargs: Any) -> RewardEventSpec:
    return RewardEventSpec(event_type, lifecycle_stage, **kwargs)


EVENT_SPECS: dict[str, RewardEventSpec] = {
    EVENT_SUBSYSTEM_DISCOVERED: _spec(EVENT_SUBSYSTEM_DISCOVERED),
    EVENT_SUBSYSTEM_PROMOTED: _spec(
        EVENT_SUBSYSTEM_PROMOTED,
        requires_governance_mission_id=True,
        requires_promotion_organ_id=True,
    ),
    EVENT_SUBSYSTEM_ADOPTED: _spec(EVENT_SUBSYSTEM_ADOPTED, requires_promotion_organ_id=True),
    EVENT_WORKFLOW_CHAIN_COMPLETED: _spec(EVENT_WORKFLOW_CHAIN_COMPLETED),
    EVENT_WORKFLOW_LIBRARY_ADMITTED: _spec(EVENT_WORKFLOW_LIBRARY_ADMITTED),
    EVENT_PROVIDER_ORGAN_ADMITTED: _spec(
        EVENT_PROVIDER_ORGAN_ADMITTED,
        requires_governance_mission_id=True,
    ),
    EVENT_SUBSYSTEM_ORGAN_PROMOTED: _spec(EVENT_SUBSYSTEM_ORGAN_PROMOTED),
    EVENT_PROOF_PACKET_PUBLISHED: _spec(EVENT_PROOF_PACKET_PUBLISHED),
    EVENT_TRUST_BUNDLE_PASSED: _spec(EVENT_TRUST_BUNDLE_PASSED),
    EVENT_CLOUD_INVARIANT_SET_PASSED: _spec(EVENT_CLOUD_INVARIANT_SET_PASSED),
    EVENT_CAPABILITY_BRIDGE_EXECUTED: _spec(EVENT_CAPABILITY_BRIDGE_EXECUTED),
    EVENT_CAPABILITY_MODULE_ADMITTED: _spec(EVENT_CAPABILITY_MODULE_ADMITTED),
    EVENT_PATTERN_CLAIM_ACCEPTED: _spec(EVENT_PATTERN_CLAIM_ACCEPTED),
    EVENT_SUBSTRATE_ENVELOPE_ATTACHED: _spec(EVENT_SUBSTRATE_ENVELOPE_ATTACHED),
    EVENT_RAIL_CREDITS_PURCHASED: _spec(
        EVENT_RAIL_CREDITS_PURCHASED,
        requires_contribution_id=False,
        requires_purchase_receipt=True,
    ),
}


def get_event_spec(event_type: str) -> RewardEventSpec | None:
    return EVENT_SPECS.get(str(event_type or "").strip())
