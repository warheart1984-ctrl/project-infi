"""Chat Turn Governance Organ — UL substrate and admission posture."""

from __future__ import annotations

from typing import Any

from src.chat_turn_governance import (
    CHAT_TURN_CONTRACT_VERSION,
    CHAT_TURN_SURFACE,
)

MODULE_ID = "AAIS-CTG-01"
ORGAN_VERSION = "chat_turn_governance_organ.v1"


def build_chat_turn_governance_status() -> dict[str, Any]:
    summary = (
        f"surface={CHAT_TURN_SURFACE};"
        f"contract={CHAT_TURN_CONTRACT_VERSION};read_only=1"
    )[:128]
    return {
        "chat_turn_governance_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "chat_turn_surface": CHAT_TURN_SURFACE,
        "contract_version": CHAT_TURN_CONTRACT_VERSION,
        "admission_read_only": True,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
