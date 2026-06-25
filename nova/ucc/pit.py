"""UCC-aligned PIT transform enrichments."""

from __future__ import annotations

from typing import Any

from nova.law_kernel.models import Intent, LawContext


def enrich_pit2_ucc(payload: dict[str, Any], intent: Intent, context: LawContext) -> None:
    inferred_intent = str(intent.payload.get("task") or intent.payload.get("intent") or "info")
    pacing = str(intent.payload.get("pacing_mode") or intent.payload.get("user_pacing") or "steady")
    payload["reflection"] = {
        "intent": inferred_intent,
        "reasoning_steps": [
            "clarify user intent",
            "reduce ambiguity",
            "apply emotional neutrality",
            "match pacing preference",
        ],
        "ambiguity_removed": True,
        "pacing": pacing,
        "emotional_neutrality": True,
    }
    payload["ucc_enabled"] = True


def enrich_pit3_ucc(payload: dict[str, Any], intent: Intent, context: LawContext) -> None:
    task = str(intent.payload.get("task") or intent.payload.get("tool_name") or "action")
    payload["plan"] = {
        "steps": [
            f"validate {task} prerequisites",
            f"execute {task}",
            "verify outcome",
            "emit lineage proof",
        ],
        "safety_checks": ["overload_below_threshold", "pacing_consent_granted", "boundary_clear"],
        "boundary_conditions": ["user_explicit_approval"],
        "rollback": "undo_last_step",
    }
    payload["ucc_enabled"] = True


def ucc_enabled(intent: Intent) -> bool:
    return bool(intent.payload.get("ucc_enabled", True))
