"""Direct Challenge Organ — read-only relational lane posture."""

from __future__ import annotations

from typing import Any

from src.direct_challenge_module import (
    DIRECT_CHALLENGE_MODULE_ID,
    DIRECT_CHALLENGE_MODULE_VERSION,
)

MODULE_ID = "AAIS-DC-01"
ORGAN_VERSION = "direct_challenge_organ.v1"


def build_direct_challenge_status() -> dict[str, Any]:
    summary = (
        f"module={DIRECT_CHALLENGE_MODULE_ID};version={DIRECT_CHALLENGE_MODULE_VERSION};"
        "severity_heuristic=1;read_only=1"
    )[:128]
    return {
        "direct_challenge_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "direct_challenge_module_id": DIRECT_CHALLENGE_MODULE_ID,
        "direct_challenge_module_version": DIRECT_CHALLENGE_MODULE_VERSION,
        "severity_heuristic": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
