from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import List, Literal, Set

AccumulationType = Literal["A1", "A2", "A3", "A4", "NONE"]
Layer = Literal["Continuity", "Transferability", "Governance", "Meta"]


@dataclass
class JPSSContributionEvent:
    id: str
    actor: str
    timestamp: str
    source_text: str
    from_exposure: bool
    accumulation_type: AccumulationType
    targets_layer: Layer
    builds_on: List[str]


@dataclass
class RAState:
    events: List[JPSSContributionEvent] = field(default_factory=list)
    accumulation_count: int = 0
    multi_person_actors: Set[str] = field(default_factory=set)


def initial_state() -> RAState:
    return RAState()


def ingest_event(state: RAState, ev: JPSSContributionEvent) -> RAState:
    is_accum = ev.accumulation_type != "NONE"
    new_accum_count = state.accumulation_count + (1 if is_accum else 0)
    new_actors = set(state.multi_person_actors)
    if is_accum:
        new_actors.add(ev.actor)
    return RAState(
        events=state.events + [ev],
        accumulation_count=new_accum_count,
        multi_person_actors=new_actors,
    )


def has_reached_mat3(state: RAState) -> bool:
    distinct_actors = len(state.multi_person_actors)
    has_a2_or_higher = any(
        e.accumulation_type in ("A2", "A3", "A4") for e in state.events
    )
    return (
        state.accumulation_count >= 3
        and distinct_actors >= 2
        and has_a2_or_higher
    )


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
