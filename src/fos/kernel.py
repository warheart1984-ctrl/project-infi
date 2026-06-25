"""FOS v0.1 minimal continuity substrate.

FOS is the governed civilization memory layer. The minimal kernel provides
continuity threads, evidence-bearing events, memory-object invariant checks,
lineage traversal, decision reconstruction, and a CAB projection bridge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4


class EventType(str, Enum):
    CONCEPT = "Concept"
    INVARIANT = "Invariant"
    ARCHITECTURE = "Architecture"
    GOVERNANCE = "Governance"
    DECISION = "Decision"
    EVIDENCE = "Evidence"
    NOTE = "Note"
    CUSTOM = "Custom"


@dataclass(frozen=True)
class ContinuityThread:
    id: str
    parent: str | None
    label: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent": self.parent,
            "label": self.label,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ContinuityThread:
        return cls(
            id=str(payload["id"]),
            parent=payload.get("parent"),
            label=payload.get("label"),
            created_at=str(payload["created_at"]),
        )


@dataclass(frozen=True)
class ContinuityEvent:
    id: str
    thread_id: str
    event_type: EventType
    payload: dict[str, Any]
    timestamp: str
    lineage: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "event_type": self.event_type.value,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
            "lineage": list(self.lineage),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ContinuityEvent:
        return cls(
            id=str(payload["id"]),
            thread_id=str(payload["thread_id"]),
            event_type=EventType(str(payload["event_type"])),
            payload=dict(payload["payload"]),
            timestamp=str(payload["timestamp"]),
            lineage=[str(item) for item in payload.get("lineage", [])],
        )


@dataclass(frozen=True)
class MemoryObjectRef:
    event_id: str
    event_type: EventType


@dataclass(frozen=True)
class FOSMemoryObject:
    id: str
    type: str
    definition: str
    evidence_refs: list[str]
    lineage: list[str]
    version: str
    continuity_thread: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "definition": self.definition,
            "evidence_refs": list(self.evidence_refs),
            "lineage": list(self.lineage),
            "version": self.version,
            "continuity_thread": self.continuity_thread,
        }


@dataclass(frozen=True)
class DecisionReconstruction:
    decision: ContinuityEvent
    thread: ContinuityThread
    discussion_events: list[ContinuityEvent]
    architecture_events: list[ContinuityEvent]
    governance_events: list[ContinuityEvent]
    evidence_events: list[ContinuityEvent]
    alternative_decisions: list[ContinuityEvent]
    outcome_events: list[ContinuityEvent]


class ContinuityStore(Protocol):
    def create_thread(self, thread: ContinuityThread) -> None: ...
    def get_thread(self, thread_id: str) -> ContinuityThread | None: ...
    def list_threads(self) -> list[ContinuityThread]: ...
    def append_event(self, event: ContinuityEvent) -> None: ...
    def get_event(self, event_id: str) -> ContinuityEvent | None: ...
    def list_events_for_thread(self, thread_id: str) -> list[ContinuityEvent]: ...


class InMemoryStore:
    def __init__(self) -> None:
        self.threads: dict[str, ContinuityThread] = {}
        self.events: dict[str, ContinuityEvent] = {}

    def create_thread(self, thread: ContinuityThread) -> None:
        self.threads[thread.id] = thread

    def get_thread(self, thread_id: str) -> ContinuityThread | None:
        return self.threads.get(thread_id)

    def list_threads(self) -> list[ContinuityThread]:
        return list(self.threads.values())

    def append_event(self, event: ContinuityEvent) -> None:
        self.events[event.id] = event

    def get_event(self, event_id: str) -> ContinuityEvent | None:
        return self.events.get(event_id)

    def list_events_for_thread(self, thread_id: str) -> list[ContinuityEvent]:
        return [event for event in self.events.values() if event.thread_id == thread_id]


class FileStore(InMemoryStore):
    """JSONL-backed store for local development and replay tests."""

    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root
        self.threads_path = root / "threads.jsonl"
        self.events_path = root / "events.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)
        self._load()

    def create_thread(self, thread: ContinuityThread) -> None:
        super().create_thread(thread)
        self._append_jsonl(self.threads_path, thread.to_dict())

    def append_event(self, event: ContinuityEvent) -> None:
        super().append_event(event)
        self._append_jsonl(self.events_path, event.to_dict())

    def _load(self) -> None:
        if self.threads_path.exists():
            for line in self.threads_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    thread = ContinuityThread.from_dict(json.loads(line))
                    self.threads[thread.id] = thread
        if self.events_path.exists():
            for line in self.events_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    event = ContinuityEvent.from_dict(json.loads(line))
                    self.events[event.id] = event

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def validate_memory_object(obj: FOSMemoryObject) -> list[str]:
    errors: list[str] = []
    if not obj.id:
        errors.append("missing id")
    if not obj.type:
        errors.append("missing type")
    if not obj.definition:
        errors.append("missing definition")
    if not obj.evidence_refs:
        errors.append("missing evidence_refs")
    if not obj.lineage:
        errors.append("missing lineage")
    if not obj.version:
        errors.append("missing version")
    if not obj.continuity_thread:
        errors.append("missing continuity_thread")
    return errors


class FOSKernel:
    def __init__(self, store: ContinuityStore | None = None) -> None:
        self.store = store or InMemoryStore()

    def create_thread(self, label: str | None = None, parent: str | None = None) -> ContinuityThread:
        if parent is not None and self.store.get_thread(parent) is None:
            raise ValueError(f"parent thread does not exist: {parent}")
        thread = ContinuityThread(
            id=f"thread:{uuid4()}",
            parent=parent,
            label=label,
            created_at=utc_now(),
        )
        self.store.create_thread(thread)
        return thread

    def append_event(
        self,
        thread_id: str,
        event_type: EventType,
        payload: dict[str, Any],
        lineage: list[str] | None = None,
        event_id: str | None = None,
    ) -> ContinuityEvent:
        if self.store.get_thread(thread_id) is None:
            raise ValueError(f"thread does not exist: {thread_id}")
        parent_ids = list(lineage or [])
        for parent in parent_ids:
            if self.store.get_event(parent) is None:
                raise ValueError(f"lineage event does not exist: {parent}")
        event = ContinuityEvent(
            id=event_id or f"event:{uuid4()}",
            thread_id=thread_id,
            event_type=event_type,
            payload=dict(payload),
            timestamp=utc_now(),
            lineage=parent_ids,
        )
        self.store.append_event(event)
        return event

    def get_thread(self, thread_id: str) -> ContinuityThread | None:
        return self.store.get_thread(thread_id)

    def list_threads(self) -> list[ContinuityThread]:
        return sorted(self.store.list_threads(), key=lambda thread: thread.created_at)

    def get_event(self, event_id: str) -> ContinuityEvent | None:
        return self.store.get_event(event_id)

    def list_events_for_thread(self, thread_id: str) -> list[ContinuityEvent]:
        return sorted(self.store.list_events_for_thread(thread_id), key=lambda event: event.timestamp)

    def get_lineage_chain(self, start_event_id: str) -> list[ContinuityEvent]:
        visited: set[str] = set()
        ordered: list[ContinuityEvent] = []

        def visit(event_id: str) -> None:
            if event_id in visited:
                return
            event = self.store.get_event(event_id)
            if event is None:
                return
            visited.add(event_id)
            for parent_id in event.lineage:
                visit(parent_id)
            ordered.append(event)

        visit(start_event_id)
        return ordered

    def memory_ref(self, event_id: str) -> MemoryObjectRef:
        event = self.store.get_event(event_id)
        if event is None:
            raise ValueError(f"event does not exist: {event_id}")
        return MemoryObjectRef(event_id=event.id, event_type=event.event_type)

    def memory_object_from_event(self, event: ContinuityEvent, version: str = "v0.1") -> FOSMemoryObject:
        definition = str(
            event.payload.get("definition")
            or event.payload.get("rationale")
            or event.payload.get("summary")
            or event.payload.get("text")
            or event.payload.get("narrative")
            or event.payload
        )
        evidence_refs = [str(item) for item in event.payload.get("evidence_refs", [])]
        if event.event_type == EventType.EVIDENCE:
            evidence_refs = [event.id]
        lineage = list(event.lineage)
        if event.event_type == EventType.EVIDENCE and not lineage:
            lineage = [event.id]
        return FOSMemoryObject(
            id=event.id,
            type=event.event_type.value,
            definition=definition,
            evidence_refs=evidence_refs,
            lineage=lineage,
            version=version,
            continuity_thread=event.thread_id,
        )

    def validate_event_as_memory_object(self, event_id: str) -> list[str]:
        event = self.store.get_event(event_id)
        if event is None:
            return ["event not found"]
        return validate_memory_object(self.memory_object_from_event(event))

    def reconstruct_decision(self, decision_id: str) -> DecisionReconstruction:
        decision = self.store.get_event(decision_id)
        if decision is None:
            raise ValueError(f"decision event not found: {decision_id}")
        if decision.event_type != EventType.DECISION:
            raise ValueError(f"event is not a decision: {decision_id}")
        thread = self.store.get_thread(decision.thread_id)
        if thread is None:
            raise ValueError(f"thread not found: {decision.thread_id}")

        discussion_events: list[ContinuityEvent] = []
        architecture_events: list[ContinuityEvent] = []
        governance_events: list[ContinuityEvent] = []
        evidence_events: list[ContinuityEvent] = []
        alternative_decisions: list[ContinuityEvent] = []

        for event in self.get_lineage_chain(decision.id):
            if event.id == decision.id:
                continue
            if event.event_type == EventType.ARCHITECTURE:
                architecture_events.append(event)
            elif event.event_type == EventType.GOVERNANCE:
                governance_events.append(event)
            elif event.event_type == EventType.EVIDENCE:
                evidence_events.append(event)
            elif event.event_type == EventType.DECISION:
                alternative_decisions.append(event)
            else:
                discussion_events.append(event)

        outcome_events = [
            event
            for event in self.list_events_for_thread(thread.id)
            if event.id != decision.id and (decision.id in event.lineage or event.timestamp > decision.timestamp)
        ]
        return DecisionReconstruction(
            decision=decision,
            thread=thread,
            discussion_events=discussion_events,
            architecture_events=architecture_events,
            governance_events=governance_events,
            evidence_events=evidence_events,
            alternative_decisions=alternative_decisions,
            outcome_events=outcome_events,
        )

    def project_cab_ledger(self, ledger: Any, label: str = "CAB projection") -> ContinuityThread:
        thread = self.create_thread(label=label)
        object_to_event: dict[str, str] = {}
        for entry in sorted(ledger.entries, key=lambda item: item.sequence):
            event_type = self._event_type_for_cab(entry.object_type.value)
            lineage = [
                object_to_event[parent]
                for parent in self._cab_parent_refs(entry.payload)
                if parent in object_to_event
            ]
            event = self.append_event(
                thread.id,
                event_type,
                {
                    "cab_object_type": entry.object_type.value,
                    "cab_object_id": entry.object_id,
                    **dict(entry.payload),
                },
                lineage=lineage,
                event_id=f"fos:{entry.object_id}",
            )
            object_to_event[entry.object_id] = event.id
        return thread

    def _event_type_for_cab(self, object_type: str) -> EventType:
        if object_type == "DecisionRecord":
            return EventType.DECISION
        if object_type == "EvidenceChain":
            return EventType.EVIDENCE
        if object_type in {"ContinuityReceipt", "ReconstructionPlan"}:
            return EventType.EVIDENCE
        if object_type in {"AssumptionRecord", "FounderKnowledgeSnapshot", "IntentRecord"}:
            return EventType.CONCEPT
        if object_type == "SuccessionProtocol":
            return EventType.GOVERNANCE
        return EventType.CUSTOM

    def _cab_parent_refs(self, payload: dict[str, Any]) -> list[str]:
        refs: list[str] = []
        for key in (
            "intent_refs",
            "prior_intent_refs",
            "decision_refs",
            "evidence_chain_refs",
            "assumption_refs",
            "continuity_receipt_refs",
            "reconstruction_plan_refs",
            "minimal_object_refs",
        ):
            refs.extend(str(item) for item in payload.get(key, []))
        return refs
