"""Immune Observe Organ — read-only observe_protocol_signal posture."""

# Mythic: Immune Observe Organ
# Engineering: ImmuneObserveEngine
from __future__ import annotations

from typing import Any

from src.immune_system import immune_system

MODULE_ID = "AAIS-IO-01"
ORGAN_VERSION = "immune_observe_organ.v1"


def build_immune_observe_status() -> dict[str, Any]:
    """Bounded immune observe snapshot; no escalation authority on organ surface."""
    snapshot = immune_system.snapshot(limit_events=6, limit_incidents=3)
    mode = str(snapshot.get("system_mode") or "normal")
    event_count = int(snapshot.get("event_count") or 0)
    observe_only = True
    summary = f"mode={mode};events={event_count};observe_only={observe_only}"[:128]
    return {
        "immune_observe_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "system_mode": mode,
        "event_count": event_count,
        "observe_protocol_only": observe_only,
        "autonomous_escalation_blocked": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
