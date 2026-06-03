"""Phase Gate Organ — read-only AAIS-PG-01 admission snapshot."""

# Mythic: Phase Gate Organ
# Engineering: PhaseGateGate
from __future__ import annotations

from typing import Any

from src.phase_gate import Phase, list_components, list_phase_events

MODULE_ID = "AAIS-PG-01"


def build_phase_gate_status() -> dict[str, Any]:
    """Bounded phase gate snapshot for governance and coherence fabric join."""
    components = list_components()
    histogram: dict[str, int] = {phase.value: 0 for phase in Phase}
    for component in components:
        phase_key = str(getattr(component.phase, "value", component.phase) or Phase.CONCEPT.value)
        histogram[phase_key] = histogram.get(phase_key, 0) + 1

    events = list_phase_events(limit=20)
    last_violation = ""
    for event in reversed(events):
        if str(event.get("event") or "") in {"execution_blocked", "routing_blocked"}:
            last_violation = str(event.get("reason") or event.get("check") or event.get("event"))[:128]
            break

    return {
        "phase_gate_organ_version": "phase_gate_organ.v1",
        "module_id": MODULE_ID,
        "registered_count": len(components),
        "phase_histogram": histogram,
        "last_violation_summary": last_violation or "none",
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
