"""Static law policy for Phase 1."""

from __future__ import annotations

from dataclasses import dataclass

from src.usl.types import CapabilityRequest, GuestContext

ALLOW = "allow"
DENY = "deny"
DEGRADE = "degrade"
QUARANTINE = "quarantine"

# Ceiling → allowed capability ids
CEILING_CAPABILITIES: dict[str, set[str]] = {
    "fs.basic": {"fs.read", "fs.write", "fs.stat", "fs.mkdir"},
    "fs.readonly": {"fs.read", "fs.stat"},
    "net.basic": {"net.connect", "net.dns"},
    "proc.basic": {"proc.spawn", "proc.exit"},
    "ui.basic": {"ui.present", "ui.resize", "ui.focus"},
}

PROFILE_CEILINGS: dict[str, set[str]] = {
    "daily-driver": {"fs.basic", "net.basic", "proc.basic", "ui.basic"},
    "containment": {"fs.readonly"},
}


@dataclass
class LawDecision:
    decision: str
    policy_id: str
    lawbook_id: str
    decision_reason: str
    decision_detail: str = ""


def evaluate_capability(request: CapabilityRequest) -> LawDecision:
    """Evaluate capability request against daily-driver / containment profiles."""
    profile = request.guest.profile_id
    cap_id = request.capability_id
    ceiling_id = request.ceiling_id

    policy_id = f"policy:{profile}"
    lawbook_id = "lawbook:usl-v1"

    allowed_ceilings = PROFILE_CEILINGS.get(profile)
    if allowed_ceilings is None:
        return LawDecision(
            decision=DENY,
            policy_id=policy_id,
            lawbook_id=lawbook_id,
            decision_reason="unknown_profile",
            decision_detail=f"profile {profile} not recognized",
        )

    if ceiling_id not in allowed_ceilings:
        return LawDecision(
            decision=DENY,
            policy_id=policy_id,
            lawbook_id=lawbook_id,
            decision_reason="ceiling_exceeded",
            decision_detail=f"ceiling {ceiling_id} not allowed for {profile}",
        )

    ceiling_caps = CEILING_CAPABILITIES.get(ceiling_id, set())
    if cap_id not in ceiling_caps:
        return LawDecision(
            decision=DENY,
            policy_id=policy_id,
            lawbook_id=lawbook_id,
            decision_reason="capability_denied",
            decision_detail=f"{cap_id} not in ceiling {ceiling_id}",
        )

    if profile == "containment" and cap_id.startswith("proc."):
        return LawDecision(
            decision=QUARANTINE,
            policy_id=policy_id,
            lawbook_id=lawbook_id,
            decision_reason="containment_proc",
            decision_detail="proc capabilities quarantined under containment profile",
        )

    return LawDecision(
        decision=ALLOW,
        policy_id=policy_id,
        lawbook_id=lawbook_id,
        decision_reason="policy_allow",
        decision_detail=f"{cap_id} permitted under {ceiling_id}",
    )
