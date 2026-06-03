"""Reasoning Executive Organ — read-only jarvis.reasoning OODA posture."""

# Mythic: Reasoning Executive Organ
# Engineering: ReasoningExecutiveEngine
from __future__ import annotations

from typing import Any

from src.jarvis_reasoning_protocol import (
    REASONING_PROTOCOL_ID,
    REASONING_PROTOCOL_VERSION,
    REASONING_STAGES,
    reasoning_protocol_spec,
)

MODULE_ID = "AAIS-REO-01"
ORGAN_VERSION = "reasoning_executive_organ.v1"


def build_reasoning_executive_status() -> dict[str, Any]:
    spec = reasoning_protocol_spec()
    return {
        "reasoning_executive_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "runtime_id": spec.get("runtime_id") or REASONING_PROTOCOL_ID,
        "protocol_version": REASONING_PROTOCOL_VERSION,
        "stages": list(REASONING_STAGES),
        "summary": str(spec.get("summary") or "")[:128],
        "executive_authority": "jarvis",
        "read_only": True,
        "routing_usurpation": False,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
