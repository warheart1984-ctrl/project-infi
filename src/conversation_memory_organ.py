"""Conversation Memory Organ — read-only session memory posture."""

from __future__ import annotations

from typing import Any

from src import conversation_memory as cm

MODULE_ID = "AAIS-CMO-01"
ORGAN_VERSION = "conversation_memory_organ.v1"


def build_conversation_memory_status() -> dict[str, Any]:
    persona_modes = len(getattr(cm, "PERSONA_DIRECTIVES", {}) or {})
    response_modes = len(getattr(cm, "RESPONSE_MODE_DIRECTIVES", {}) or {})
    summary = (
        f"persona_modes={persona_modes};response_modes={response_modes};read_only=1"
    )[:128]
    return {
        "conversation_memory_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "persona_directive_count": persona_modes,
        "response_mode_directive_count": response_modes,
        "memory_board_law_single_path": False,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
