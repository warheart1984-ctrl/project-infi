"""Predictor Immune Bridge Organ — Alt-9 producer to immune observe attestation."""

from __future__ import annotations

from typing import Any

from src.immune_observe_organ import build_immune_observe_status
from src.realtime_event_cause_predictor_organ import build_realtime_predictor_status

MODULE_ID = "AAIS-PIB-01"
ORGAN_VERSION = "predictor_immune_bridge_organ.v1"


def build_predictor_immune_bridge_status(
    *,
    governed_pipeline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attest predictor producer path joins immune observe substrate (observe-only)."""
    predictor = build_realtime_predictor_status(governed_pipeline=governed_pipeline)
    immune = build_immune_observe_status()
    producer = bool(predictor.get("live_runtime_producer"))
    observe_only = bool(immune.get("observe_protocol_only"))
    bridged = producer and observe_only
    summary = (
        f"producer={producer};immune_observe={observe_only};bridged={bridged}"
    )[:128]
    return {
        "predictor_immune_bridge_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "predictor_producer_attested": producer,
        "immune_observe_only": observe_only,
        "substrate_bridged": bridged,
        "autonomous_escalation_blocked": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
