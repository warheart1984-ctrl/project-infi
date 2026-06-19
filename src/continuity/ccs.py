"""Core Continuity Substrate (CCS) types and store."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Identity:
    id: str
    kind: str
    display_name: str
    lineage: dict[str, Any]
    authority_surface: dict[str, Any]
    cultural_surface: dict[str, Any]
    technical_surface: dict[str, Any]


@dataclass(frozen=True)
class Event:
    id: str
    kind: str
    actors: list[str]
    targets: list[str]
    time: dict[str, Any]
    context: dict[str, Any]
    law_surface: dict[str, Any]
    description: str
    linked_evaluations: list[str] = field(default_factory=list)
    linked_evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Evaluation:
    id: str
    kind: str
    evaluator_id: str
    evaluated_event_ids: list[str]
    law_surface: dict[str, Any]
    finding: str
    reasoning: str
    uncertainty: int
    risks: list[str]
    recommended_actions: list[str]
    linked_evidence_ids: list[str]


@dataclass(frozen=True)
class Evidence:
    id: str
    type: str
    source: str
    integrity: dict[str, Any]
    linked_identity_ids: list[str]
    linked_event_ids: list[str]
    law_surface: dict[str, Any]
    payload_ref: str


@dataclass(frozen=True)
class ContinuityTrace:
    id: str
    scope: dict[str, Any]
    timeline: list[dict[str, Any]]
    law_surfaces: dict[str, Any]
    continuity_summary: dict[str, Any]
    reproducibility_metadata: dict[str, Any]


class CCSStore:
    def __init__(self) -> None:
        self.identities: dict[str, Identity] = {}
        self.events: dict[str, Event] = {}
        self.evaluations: dict[str, Evaluation] = {}
        self.evidence: dict[str, Evidence] = {}
        self.traces: dict[str, ContinuityTrace] = {}

    def add_identity(self, identity: Identity) -> None:
        if identity.id in self.identities:
            raise ValueError(f"duplicate identity: {identity.id}")
        self.identities[identity.id] = identity

    def add_event(self, event: Event) -> None:
        if event.id in self.events:
            raise ValueError(f"duplicate event: {event.id}")
        self.events[event.id] = event

    def add_evaluation(self, evaluation: Evaluation) -> None:
        if evaluation.id in self.evaluations:
            raise ValueError(f"duplicate evaluation: {evaluation.id}")
        self.evaluations[evaluation.id] = evaluation

    def add_evidence(self, evidence: Evidence) -> None:
        if evidence.id in self.evidence:
            raise ValueError(f"duplicate evidence: {evidence.id}")
        self.evidence[evidence.id] = evidence

    def add_trace(self, trace: ContinuityTrace) -> None:
        if trace.id in self.traces:
            raise ValueError(f"duplicate trace: {trace.id}")
        self.traces[trace.id] = trace


def law_surface_has_law(law_surface: dict[str, Any]) -> bool:
    return bool(law_surface.get("aais_laws") or law_surface.get("csleis_laws") or law_surface.get("other_laws"))


def identity_from_object(obj: dict[str, Any]) -> Identity:
    spec = obj["spec"]
    return Identity(
        id=obj["metadata"]["id"],
        kind=spec["kind"],
        display_name=spec["display_name"],
        lineage=spec["lineage"],
        authority_surface=spec["authority_surface"],
        cultural_surface=spec["cultural_surface"],
        technical_surface=spec["technical_surface"],
    )


def event_from_object(obj: dict[str, Any]) -> Event:
    spec = obj["spec"]
    return Event(
        id=obj["metadata"]["id"],
        kind=spec["kind"],
        actors=spec["actors"],
        targets=spec["targets"],
        time=spec["time"],
        context=spec["context"],
        law_surface=spec["law_surface"],
        description=spec["description"],
        linked_evaluations=spec.get("linked_evaluations", []),
        linked_evidence=spec.get("linked_evidence", []),
    )


def evaluation_from_object(obj: dict[str, Any]) -> Evaluation:
    spec = obj["spec"]
    return Evaluation(
        id=obj["metadata"]["id"],
        kind=spec["kind"],
        evaluator_id=spec["evaluator_id"],
        evaluated_event_ids=spec["evaluated_event_ids"],
        law_surface=spec["law_surface"],
        finding=spec["finding"],
        reasoning=spec["reasoning"],
        uncertainty=spec["uncertainty"],
        risks=spec["risks"],
        recommended_actions=spec["recommended_actions"],
        linked_evidence_ids=spec["linked_evidence_ids"],
    )


def evidence_from_object(obj: dict[str, Any]) -> Evidence:
    spec = obj["spec"]
    return Evidence(
        id=obj["metadata"]["id"],
        type=spec["type"],
        source=spec["source"],
        integrity=spec["integrity"],
        linked_identity_ids=spec["linked_identity_ids"],
        linked_event_ids=spec["linked_event_ids"],
        law_surface=spec["law_surface"],
        payload_ref=spec["payload_ref"],
    )


def trace_from_object(obj: dict[str, Any]) -> ContinuityTrace:
    spec = obj["spec"]
    return ContinuityTrace(
        id=obj["metadata"]["id"],
        scope=spec["scope"],
        timeline=spec["timeline"],
        law_surfaces=spec["law_surfaces"],
        continuity_summary=spec["continuity_summary"],
        reproducibility_metadata=spec["reproducibility_metadata"],
    )


def load_scenario(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_store_from_scenario(scenario: dict[str, Any]) -> CCSStore:
    store = CCSStore()
    for obj in scenario.get("identities", []):
        store.add_identity(identity_from_object(obj))
    for obj in scenario.get("events", []):
        store.add_event(event_from_object(obj))
    for obj in scenario.get("evaluations", []):
        store.add_evaluation(evaluation_from_object(obj))
    for obj in scenario.get("evidence", []):
        store.add_evidence(evidence_from_object(obj))
    return store


def continuity_trace_fingerprint(trace: ContinuityTrace) -> str:
    payload = {
        "id": trace.id,
        "scope": trace.scope,
        "timeline": trace.timeline,
        "law_surfaces": trace.law_surfaces,
        "continuity_summary": trace.continuity_summary,
        "reproducibility_metadata": trace.reproducibility_metadata,
    }
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def replay_trace_from_store(store: CCSStore, trace: ContinuityTrace) -> ContinuityTrace:
    """Reconstruct a ContinuityTrace from CCS objects using the trace timeline as canonical order."""
    timeline: list[dict[str, Any]] = []
    for item in trace.timeline:
        event_id = item["event_id"]
        if event_id not in store.events:
            raise KeyError(f"missing event for replay: {event_id}")
        evaluation_ids = sorted(
            evaluation_id
            for evaluation_id in item.get("evaluations", [])
            if evaluation_id in store.evaluations
        )
        evidence_ids = sorted(
            evidence_id
            for evidence_id in item.get("evidence", [])
            if evidence_id in store.evidence
        )
        timeline.append(
            {
                "event_id": event_id,
                "evaluations": evaluation_ids,
                "evidence": evidence_ids,
            }
        )

    return ContinuityTrace(
        id=trace.id,
        scope=trace.scope,
        timeline=timeline,
        law_surfaces=trace.law_surfaces,
        continuity_summary=trace.continuity_summary,
        reproducibility_metadata=trace.reproducibility_metadata,
    )
