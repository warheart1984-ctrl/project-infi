"""Stewardability Register — ledger of events affecting steward generation capacity."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

StewardEventKind = Literal[
    "EMERGENCE",
    "DEMONSTRATION",
    "BLOCKAGE",
    "SUCCESSION",
    "FAILURE",
    "RECOVERY",
]

UncertaintyLevel = Literal["LOW", "MEDIUM", "HIGH"]
LineageImpact = Literal["STRENGTHENED", "UNCHANGED", "WEAKENED"]


class StewardContext(BaseModel):
    environment_id: str
    novelty_profile: list[str] = Field(default_factory=list)
    conflict_profile: list[str] = Field(default_factory=list)
    uncertainty_level: UncertaintyLevel = "MEDIUM"


class StewardDemonstration(BaseModel):
    steward_id: str
    questions_asked: list[str] = Field(default_factory=list)
    reconstructions: list[str] = Field(default_factory=list)
    critiques: list[str] = Field(default_factory=list)
    adaptations: list[str] = Field(default_factory=list)
    lineage_impact: LineageImpact = "UNCHANGED"


class StewardabilityEvent(BaseModel):
    id: str
    kind: StewardEventKind
    timestamp: datetime
    context: StewardContext
    demonstration: StewardDemonstration | None = None
    notes: str | None = None


class StewardAbilityRegister(BaseModel):
    events: list[StewardabilityEvent] = Field(default_factory=list)

    def append(self, event: StewardabilityEvent) -> None:
        self.events.append(event)

    def emergence_events(self) -> list[StewardabilityEvent]:
        return [event for event in self.events if event.kind == "EMERGENCE"]

    def demonstration_events(self) -> list[StewardabilityEvent]:
        return [event for event in self.events if event.kind == "DEMONSTRATION"]

    def blockage_events(self) -> list[StewardabilityEvent]:
        return [event for event in self.events if event.kind == "BLOCKAGE"]


def new_event_id() -> str:
    return f"event-{uuid4().hex[:12]}"


def demonstration_context_from(demo: StewardDemonstration) -> StewardContext:
    return StewardContext(
        environment_id="env-unknown",
        novelty_profile=["UNSPECIFIED"],
        conflict_profile=["UNSPECIFIED"],
        uncertainty_level="MEDIUM",
    )


def record_event(
    register: StewardAbilityRegister,
    *,
    kind: StewardEventKind,
    context: StewardContext,
    demonstration: StewardDemonstration | None = None,
    notes: str | None = None,
    timestamp: datetime | None = None,
) -> StewardabilityEvent:
    event = StewardabilityEvent(
        id=new_event_id(),
        kind=kind,
        timestamp=timestamp or datetime.now(UTC).replace(microsecond=0),
        context=context,
        demonstration=demonstration,
        notes=notes,
    )
    register.append(event)
    return event
