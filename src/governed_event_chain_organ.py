"""Governed Event Chain Organ — read-only predictor→invariant→immune chain posture."""

# Mythic: Governed Event Chain Organ
# Engineering: GovernedEventChainEngine
from __future__ import annotations

from typing import Any

from src.governed_event_chain import (
    CHAIN_COMPONENT_ID,
    CHAIN_DECISION_ALLOW,
    CHAIN_DECISION_BLOCK,
    CHAIN_STATUS_BLOCKED,
    CHAIN_STATUS_PROCEED,
    MODULE_ID as CHAIN_MODULE_ID,
    MODULE_VERSION as CHAIN_MODULE_VERSION,
)
from src.phase_gate import get_component, is_executable

MODULE_ID = "AAIS-GEC-01"
ORGAN_VERSION = "governed_event_chain_organ.v1"


def build_governed_event_chain_status() -> dict[str, Any]:
    """Bounded governed event chain posture; observe-only at immune boundary."""
    registered = False
    executable = False
    try:
        registered = get_component(CHAIN_COMPONENT_ID) is not None
        executable = is_executable(CHAIN_COMPONENT_ID)
    except Exception:
        registered = False
        executable = False
    summary = (
        f"chain={CHAIN_MODULE_ID};registered={registered};"
        f"executable={executable};observe_only=1"
    )[:128]
    return {
        "governed_event_chain_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "chain_module_id": CHAIN_MODULE_ID,
        "chain_module_version": CHAIN_MODULE_VERSION,
        "chain_component_id": CHAIN_COMPONENT_ID,
        "component_registered": registered,
        "component_executable": executable,
        "allowed_decisions": [CHAIN_DECISION_ALLOW, CHAIN_DECISION_BLOCK],
        "allowed_statuses": [CHAIN_STATUS_PROCEED, CHAIN_STATUS_BLOCKED],
        "observe_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
