from __future__ import annotations

from typing import Dict, List

from constitutional.core.models import StateName

# Universal constitutional transition graph (Article XV)
LEGAL_TRANSITIONS: Dict[StateName, List[StateName]] = {
    "Proposed": ["Evaluated"],
    "Evaluated": ["Approved"],
    "Approved": ["Executed"],
    "Executed": ["Observed"],
    "Observed": ["Challenged", "Closed"],
    "Challenged": ["Arbitrated"],
    "Arbitrated": ["Remediated"],
    "Remediated": ["Closed"],
}

# Domain-specific labels mapped onto the universal graph
DOMAIN_STATE_MAPS: Dict[str, Dict[str, StateName]] = {
    "Truth": {
        "Supported": "Evaluated",
        "Verified": "Approved",
        "Diverged": "Challenged",
    },
    "Sovereignty": {
        "Requested": "Proposed",
        "Delegated": "Approved",
        "Active": "Executed",
        "Suspended": "Challenged",
        "Revoked": "Remediated",
    },
    "Institutional": {
        "Draft": "Proposed",
        "Audited": "Challenged",
        "Amended": "Remediated",
    },
    "Continuity": {
        "EventRecorded": "Executed",
    },
    "Reproduction": {
        "Reproduced": "Executed",
        "Diverged": "Challenged",
    },
    "mission": {
        "Proposed": "Proposed",
        "PLANNED": "Evaluated",
        "RUNNING": "Executed",
        "COMPLETED": "Observed",
    },
    "operator_task": {
        "queued": "Proposed",
        "planned": "Evaluated",
        "running": "Executed",
        "completed": "Observed",
        "closed": "Closed",
    },
    "cognitive_span": {
        "INIT": "Proposed",
        "INTENTED": "Evaluated",
        "DECIDED": "Approved",
        "EXECUTING": "Executed",
        "RESULTED": "Observed",
        "CLOSED": "Closed",
    },
    "constitutional_state": {
        "Healthy": "Observed",
        "Degraded": "Challenged",
        "Critical": "Arbitrated",
    },
}

CONSTITUTIONAL_CONDITION_TRANSITIONS: Dict[StateName, List[StateName]] = {
    "Healthy": ["Degraded"],
    "Degraded": ["Healthy", "Critical"],
    "Critical": ["Degraded"],
}


def validate_transition(from_state: StateName, to_state: StateName) -> None:
    allowed = LEGAL_TRANSITIONS.get(from_state, [])
    if to_state not in allowed:
        raise ValueError(f"Illegal transition: {from_state} → {to_state}")


def validate_constitutional_condition_transition(
    from_condition: StateName,
    to_condition: StateName,
) -> None:
    allowed = CONSTITUTIONAL_CONDITION_TRANSITIONS.get(from_condition, [])
    if to_condition not in allowed:
        raise ValueError(
            f"Illegal constitutional condition transition: {from_condition} → {to_condition}"
        )


def map_domain_state(domain: str, domain_state: str) -> StateName:
    mapping = DOMAIN_STATE_MAPS.get(domain, {})
    return mapping.get(domain_state, domain_state)
