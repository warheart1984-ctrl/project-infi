"""AE-JSON-1 — minimal schema for accumulation (compounding) events in COS-1."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from src.continuity.stewardability.lineage_event_log import (
    LineageActor,
    LineageEvent,
    LineageInsight,
    NoveltyLevel,
)

AE_JSON_SCHEMA_VERSION = "ae-json-1"
AE_JSON_SCHEMA_REFERENCE = "Accumulation Event JSON Schema (AE-JSON-1)"

AccumulationSignature = Literal["A1", "A2", "A3", "A4", "NONE"]

# ADF-1 signatures
ADF_A1 = "A1"  # explanatory deepening
ADF_A2 = "A2"  # structural deepening
ADF_A3 = "A3"  # integrative synthesis
ADF_A4 = "A4"  # generational compounding


class AccumulationInsight(BaseModel):
    """Insight block — compatible with lineage-event insight shape."""

    text: str
    lineage_compatible: bool
    novelty_level: NoveltyLevel
    structural_alignment: list[str] = Field(default_factory=list)


class AccumulationFields(BaseModel):
    """Raw accumulation properties before signature classification."""

    strengthened_explanation: bool = False
    structural_deepening: bool = False
    integrative_synthesis: bool = False
    builds_on_event_ids: list[str] = Field(default_factory=list)
    returns_stronger: bool = False


class AccumulationBlock(AccumulationFields):
    """Accumulation block with optional pre-computed signature."""

    signature: AccumulationSignature | None = None


class AccumulationEvent(BaseModel):
    """AE-JSON-1 accumulation event — subset of lineage events (ADF-1)."""

    event_id: str
    timestamp: datetime
    actor: LineageActor
    insight: AccumulationInsight
    accumulation: AccumulationBlock
    lineage_event_id: str | None = None

    @model_validator(mode="after")
    def _ensure_signature(self) -> AccumulationEvent:
        from src.cos1.accumulation.classifier import classify_accumulation

        if self.accumulation.signature is None:
            sig = classify_accumulation(self.accumulation)
            self.accumulation.signature = sig
        return self


class AccumulationEventLog(BaseModel):
    version: str = AE_JSON_SCHEMA_VERSION
    events: list[AccumulationEvent] = Field(default_factory=list)

    def append(self, event: AccumulationEvent) -> None:
        self.events.append(event)

    def accumulation_events(self) -> list[AccumulationEvent]:
        return [
            event
            for event in self.events
            if event.accumulation.signature and event.accumulation.signature != "NONE"
        ]

    def by_signature(self, signature: AccumulationSignature) -> list[AccumulationEvent]:
        return [
            event
            for event in self.events
            if event.accumulation.signature == signature
        ]


def new_accumulation_event_id(prefix: str = "ae") -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{stamp}-{uuid4().hex[:8]}"


def lineage_insight_to_accumulation(insight: LineageInsight) -> AccumulationInsight:
    return AccumulationInsight(
        text=insight.text,
        lineage_compatible=insight.lineage_compatible,
        novelty_level=insight.novelty_level,
        structural_alignment=[str(tag) for tag in insight.structural_alignment],
    )


def lineage_event_to_accumulation_shell(
    event: LineageEvent,
    *,
    accumulation: AccumulationFields | None = None,
) -> AccumulationEvent:
    """Wrap a lineage event as AE-JSON-1 with default (unclassified) accumulation fields."""
    fields = accumulation or AccumulationFields()
    return AccumulationEvent(
        event_id=event.event_id,
        timestamp=event.timestamp,
        actor=event.actor,
        insight=lineage_insight_to_accumulation(event.insight),
        accumulation=AccumulationBlock(**fields.model_dump()),
        lineage_event_id=event.event_id,
    )


def record_accumulation_event(
    log: AccumulationEventLog,
    *,
    actor: LineageActor,
    insight: AccumulationInsight,
    accumulation: AccumulationFields,
    event_id: str | None = None,
    timestamp: datetime | None = None,
    lineage_event_id: str | None = None,
) -> AccumulationEvent:
    event = AccumulationEvent(
        event_id=event_id or new_accumulation_event_id(),
        timestamp=timestamp or datetime.now(UTC).replace(microsecond=0),
        actor=actor,
        insight=insight,
        accumulation=AccumulationBlock(**accumulation.model_dump()),
        lineage_event_id=lineage_event_id,
    )
    log.append(event)
    return event
