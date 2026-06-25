"""CE-JSON-1 — unified event schema powering all axes and thresholds."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from src.continuity.stewardability.lineage_event_log import (
    LineageActor,
    LineageEvent,
    LineageInsight,
    LineageOrigin,
    OriginType,
)
from src.cos1.accumulation.ae_json_schema import (
    AccumulationBlock,
    AccumulationEvent,
    AccumulationFields,
    AccumulationSignature,
)
from src.cos1.accumulation.classifier import classify_accumulation
from src.cos1.continuity_engine.spec import CE1_REFERENCE

CE_JSON_SCHEMA_VERSION = "ce-json-1"


class CEAccumulationBlock(BaseModel):
    signature: AccumulationSignature = "NONE"
    builds_on_event_ids: list[str] = Field(default_factory=list)
    returns_stronger: bool = False


class ContinuityEngineEvent(BaseModel):
    """CE-JSON-1 — single event type for propagation, convergence, and accumulation."""

    event_id: str
    timestamp: datetime
    actor: LineageActor
    insight: LineageInsight
    origin: LineageOrigin
    accumulation: CEAccumulationBlock = Field(default_factory=CEAccumulationBlock)


class ContinuityEngineEventLog(BaseModel):
    version: str = CE_JSON_SCHEMA_VERSION
    reference: str = CE1_REFERENCE
    events: list[ContinuityEngineEvent] = Field(default_factory=list)

    def append(self, event: ContinuityEngineEvent) -> None:
        self.events.append(event)

    def propagation_events(self) -> list[ContinuityEngineEvent]:
        return [event for event in self.events if event.origin.type == "PROPAGATION"]

    def convergence_events(self) -> list[ContinuityEngineEvent]:
        return [event for event in self.events if event.origin.type == "CONVERGENCE"]

    def accumulation_events(self) -> list[ContinuityEngineEvent]:
        return [
            event
            for event in self.events
            if event.accumulation.signature != "NONE"
        ]


def new_ce_event_id(prefix: str = "ce") -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{stamp}-{uuid4().hex[:8]}"


def lineage_event_to_ce_event(
    event: LineageEvent,
    *,
    accumulation: AccumulationFields | None = None,
) -> ContinuityEngineEvent:
    fields = accumulation or AccumulationFields()
    signature = classify_accumulation(fields)
    return ContinuityEngineEvent(
        event_id=event.event_id,
        timestamp=event.timestamp,
        actor=event.actor,
        insight=event.insight,
        origin=event.origin,
        accumulation=CEAccumulationBlock(
            signature=signature,
            builds_on_event_ids=list(fields.builds_on_event_ids),
            returns_stronger=fields.returns_stronger,
        ),
    )


def accumulation_event_to_ce_event(event: AccumulationEvent) -> ContinuityEngineEvent:
    origin_type: OriginType = "AMBIGUOUS"
    return ContinuityEngineEvent(
        event_id=event.event_id,
        timestamp=event.timestamp,
        actor=event.actor,
        insight=LineageInsight(
            text=event.insight.text,
            lineage_compatible=event.insight.lineage_compatible,
            novelty_level=event.insight.novelty_level,
            structural_alignment=event.insight.structural_alignment,  # type: ignore[arg-type]
        ),
        origin=LineageOrigin(type=origin_type),
        accumulation=CEAccumulationBlock(
            signature=event.accumulation.signature or "NONE",
            builds_on_event_ids=list(event.accumulation.builds_on_event_ids),
            returns_stronger=event.accumulation.returns_stronger,
        ),
    )


def record_ce_event(
    log: ContinuityEngineEventLog,
    *,
    actor: LineageActor,
    insight: LineageInsight,
    origin: LineageOrigin,
    accumulation: AccumulationFields | None = None,
    event_id: str | None = None,
    timestamp: datetime | None = None,
) -> ContinuityEngineEvent:
    fields = accumulation or AccumulationFields()
    event = ContinuityEngineEvent(
        event_id=event_id or new_ce_event_id(),
        timestamp=timestamp or datetime.now(UTC).replace(microsecond=0),
        actor=actor,
        insight=insight,
        origin=origin,
        accumulation=CEAccumulationBlock(
            signature=classify_accumulation(fields),
            builds_on_event_ids=list(fields.builds_on_event_ids),
            returns_stronger=fields.returns_stronger,
        ),
    )
    log.append(event)
    return event


def build_ce_log_from_memory_logs(
    lineage_log: object,
    accumulation_log: object,
) -> ContinuityEngineEventLog:
    """Merge lineage and accumulation registers into unified CE-JSON-1 log."""
    from src.continuity.stewardability.lineage_event_log import LineageEventLog
    from src.cos1.accumulation.ae_json_schema import AccumulationEventLog

    assert isinstance(lineage_log, LineageEventLog)
    assert isinstance(accumulation_log, AccumulationEventLog)

    ce_log = ContinuityEngineEventLog()
    accumulation_by_id = {event.event_id: event for event in accumulation_log.events}

    for lineage_event in lineage_log.events:
        acc = accumulation_by_id.get(lineage_event.event_id)
        if acc is not None:
            fields = AccumulationFields(
                strengthened_explanation=acc.accumulation.strengthened_explanation,
                structural_deepening=acc.accumulation.structural_deepening,
                integrative_synthesis=acc.accumulation.integrative_synthesis,
                builds_on_event_ids=list(acc.accumulation.builds_on_event_ids),
                returns_stronger=acc.accumulation.returns_stronger,
            )
            ce_log.append(lineage_event_to_ce_event(lineage_event, accumulation=fields))
        else:
            ce_log.append(lineage_event_to_ce_event(lineage_event))

    lineage_ids = {event.event_id for event in lineage_log.events}
    for acc_event in accumulation_log.events:
        if acc_event.event_id not in lineage_ids:
            ce_log.append(accumulation_event_to_ce_event(acc_event))

    return ce_log
