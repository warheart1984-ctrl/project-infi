"""Operator Health Sentinel Organ — advisory-only burden snapshot."""

# Mythic: Operator Health Sentinel Organ
# Engineering: OperatorHealthSentinelGate
from __future__ import annotations

from typing import Any

from src.operator_health_sentinel import (
    MODULE_ID as SENTINEL_MODULE_ID,
    SENTINEL_COMPONENT_ID,
    build_operator_health_sentinel_module_spec,
)

MODULE_ID = "AAIS-OHSO-01"
ORGAN_VERSION = "operator_health_sentinel_organ.v1"


def build_operator_health_sentinel_organ_status() -> dict[str, Any]:
    spec = build_operator_health_sentinel_module_spec()
    verification = dict((spec.get("cisiv") or {}).get("verification") or {})
    verified = str(verification.get("status") or "") == "verified"
    summary = (
        f"sentinel={SENTINEL_COMPONENT_ID};advisory_only=1;verified={int(verified)}"
    )[:128]
    return {
        "operator_health_sentinel_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "sentinel_component_id": SENTINEL_COMPONENT_ID,
        "sentinel_module_id": SENTINEL_MODULE_ID,
        "advisory_only": True,
        "verification_status": str(verification.get("status") or "unknown")[:32],
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
