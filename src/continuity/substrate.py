"""ContinuitySubstrate — unified POD + CCS + ContinuityTrace layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.continuity.ccs import CCSStore, ContinuityTrace
from src.continuity.pod import PODDecision
from src.continuity.proof import Proof
from src.continuity.ugr_trace import INVARIANT_IDS

SUBSTRATE_INVARIANTS = (
    "ugr.identity_continuity",
    "ugr.authority_continuity",
    "ugr.evidence_integrity",
    "ugr.law_surface_binding",
    "ugr.continuity_unifier",
)


@dataclass
class ContinuitySubstrate:
    """POD decisions, CCS records, and ContinuityTraces as one governed substrate."""

    substrate_id: str
    pod_layer: dict[str, list[str]] = field(default_factory=lambda: {"decisions": []})
    ccs_layer: dict[str, list[str]] = field(
        default_factory=lambda: {
            "identities": [],
            "events": [],
            "evaluations": [],
            "evidence": [],
        }
    )
    trace_layer: dict[str, list[str]] = field(default_factory=lambda: {"traces": []})
    invariants: list[str] = field(default_factory=lambda: list(SUBSTRATE_INVARIANTS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "substrate_id": self.substrate_id,
            "pod_layer": {key: list(value) for key, value in self.pod_layer.items()},
            "ccs_layer": {key: list(value) for key, value in self.ccs_layer.items()},
            "trace_layer": {key: list(value) for key, value in self.trace_layer.items()},
            "invariants": list(self.invariants),
        }


def bind_pod_decision(
    substrate: ContinuitySubstrate,
    decision: PODDecision,
    *,
    event_id: str,
    evaluation_id: str | None = None,
    evidence_ids: list[str] | None = None,
    trace: ContinuityTrace | None = None,
) -> ContinuitySubstrate:
    """
  POD.Decision → CCS.Event + CCS.Evaluation + CCS.Evidence → ContinuityTrace.

    Registers references on the substrate without mutating CCS objects.
    """
    decisions = list(substrate.pod_layer.get("decisions", []))
    if decision.decision_id not in decisions:
        decisions.append(decision.decision_id)
    substrate.pod_layer["decisions"] = decisions

    events = list(substrate.ccs_layer.get("events", []))
    if event_id not in events:
        events.append(event_id)
    substrate.ccs_layer["events"] = events

    if evaluation_id:
        evaluations = list(substrate.ccs_layer.get("evaluations", []))
        if evaluation_id not in evaluations:
            evaluations.append(evaluation_id)
        substrate.ccs_layer["evaluations"] = evaluations

    if evidence_ids:
        evidence = list(substrate.ccs_layer.get("evidence", []))
        for evidence_id in evidence_ids:
            if evidence_id not in evidence:
                evidence.append(evidence_id)
        substrate.ccs_layer["evidence"] = evidence

    if trace is not None:
        traces = list(substrate.trace_layer.get("traces", []))
        if trace.id not in traces:
            traces.append(trace.id)
        substrate.trace_layer["traces"] = traces

    return substrate


def validate_substrate(store: CCSStore, substrate: ContinuitySubstrate) -> tuple[bool, list[str]]:
    """
    Every POD decision that matters must have CCS representation and a ContinuityTrace.

    Returns (valid, violations).
    """
    violations: list[str] = []

    for decision_id in substrate.pod_layer.get("decisions", []):
        if not substrate.ccs_layer.get("events"):
            violations.append(f"decision:{decision_id}:missing_ccs_events")
        if not substrate.trace_layer.get("traces"):
            violations.append(f"decision:{decision_id}:missing_continuity_trace")

    for identity_id in substrate.ccs_layer.get("identities", []):
        if identity_id not in store.identities:
            violations.append(f"missing_identity:{identity_id}")

    for event_id in substrate.ccs_layer.get("events", []):
        if event_id not in store.events:
            violations.append(f"missing_event:{event_id}")

    for evaluation_id in substrate.ccs_layer.get("evaluations", []):
        if evaluation_id not in store.evaluations:
            violations.append(f"missing_evaluation:{evaluation_id}")

    for evidence_id in substrate.ccs_layer.get("evidence", []):
        if evidence_id not in store.evidence:
            violations.append(f"missing_evidence:{evidence_id}")

    for trace_id in substrate.trace_layer.get("traces", []):
        if trace_id not in store.traces:
            violations.append(f"missing_trace:{trace_id}")

    if set(substrate.invariants) - set(INVARIANT_IDS):
        violations.append("substrate_invariants_not_ugr_aligned")

    return len(violations) == 0, violations


def index_store_layers(store: CCSStore) -> dict[str, list[str]]:
    return {
        "identities": sorted(store.identities.keys()),
        "events": sorted(store.events.keys()),
        "evaluations": sorted(store.evaluations.keys()),
        "evidence": sorted(store.evidence.keys()),
        "traces": sorted(store.traces.keys()),
    }


def substrate_from_store(store: CCSStore, *, substrate_id: str) -> ContinuitySubstrate:
    layers = index_store_layers(store)
    return ContinuitySubstrate(
        substrate_id=substrate_id,
        ccs_layer={
            "identities": layers["identities"],
            "events": layers["events"],
            "evaluations": layers["evaluations"],
            "evidence": layers["evidence"],
        },
        trace_layer={"traces": layers["traces"]},
    )
