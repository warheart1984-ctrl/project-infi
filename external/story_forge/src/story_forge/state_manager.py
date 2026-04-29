from __future__ import annotations

import hashlib

from story_forge.models import (
    ActiveEvent,
    Event,
    LocationTransition,
    ScheduledEvent,
    StoryState,
    utc_now,
)


def advance_scenario(
    state: StoryState,
    new_stage: str,
    current_turn: int,
) -> None:
    """Advance scenario to a new stage and reset counters."""
    if state.scenario_position.current_stage == new_stage:
        return
    state.scenario_position.current_stage = new_stage
    state.scenario_position.entered_stage_turn = current_turn
    state.scenario_position.stage_turn_count = 0
    state.updated_at = utc_now()


def tick_scenario(state: StoryState) -> None:
    """Increment stage turn count each turn."""
    state.scenario_position.stage_turn_count += 1
    state.updated_at = utc_now()


def transition_location(
    state: StoryState,
    to_location: str,
    cause: str,
    turn_number: int,
    forced: bool = False,
) -> None:
    """Log a location transition. No-op if already there unless forced."""
    current = state.player_state.current_location_id
    if current == to_location and not forced:
        return
    state.location_history.append(
        LocationTransition(
            from_location=current,
            to_location=to_location,
            turn_number=turn_number,
            cause=cause,
        )
    )
    state.player_state.current_location_id = to_location
    location = state.world_state.locations.get(to_location)
    if location is not None:
        location["discovered"] = True
    state.updated_at = utc_now()


def register_active_event(
    state: StoryState,
    event_id: str,
    event_type: str,
    current_turn: int,
    expires_turn: int | None = None,
    source: str = "system",
    payload: dict[str, str | int | bool] | None = None,
) -> None:
    """Register an active event. Rejects duplicate unresolved event_id."""
    for existing in state.active_events:
        if existing.event_id == event_id and not existing.resolved:
            return
    state.active_events.append(
        ActiveEvent(
            event_id=event_id,
            event_type=event_type,
            started_turn=current_turn,
            expires_turn=expires_turn,
            resolved=False,
            source=source,
            payload=payload or {},
        )
    )
    state.updated_at = utc_now()


def resolve_active_event(
    state: StoryState,
    event_id: str,
) -> bool:
    """Resolve an active event by id. Returns True if found and resolved."""
    for event in state.active_events:
        if event.event_id == event_id and not event.resolved:
            event.resolved = True
            state.updated_at = utc_now()
            return True
    return False


def expire_active_events(
    state: StoryState,
    current_turn: int,
) -> list[str]:
    """Expire unresolved events past their expiry turn.
    Returns list of expired event_ids."""
    expired = []
    for event in state.active_events:
        if (
            not event.resolved
            and event.expires_turn is not None
            and current_turn >= event.expires_turn
        ):
            event.resolved = True
            expired.append(event.event_id)
    if expired:
        state.updated_at = utc_now()
    return expired


def schedule_event(
    state: StoryState,
    event_type: str,
    trigger_turn: int,
    source_event_id: str | None = None,
    source: str = "system",
    payload: dict[str, str | int | bool] | None = None,
) -> str:
    """Schedule a future event and return its scheduled_id."""
    scheduled_id = _scheduled_event_id(event_type, trigger_turn, source_event_id)
    for existing in state.scheduled_events:
        if (
            not existing.fired
            and existing.event_type == event_type
            and existing.trigger_turn == trigger_turn
            and existing.source_event_id == source_event_id
        ):
            return existing.scheduled_id

    state.scheduled_events.append(
        ScheduledEvent(
            scheduled_id=scheduled_id,
            event_type=event_type,
            trigger_turn=trigger_turn,
            source_event_id=source_event_id,
            source=source,
            payload=payload or {},
            fired=False,
        )
    )
    state.updated_at = utc_now()
    return scheduled_id


def get_due_scheduled_events(
    state: StoryState,
    current_turn: int,
) -> list[ScheduledEvent]:
    """Return all unfired scheduled events whose trigger_turn has arrived."""
    due = [
        event
        for event in state.scheduled_events
        if not event.fired and current_turn >= event.trigger_turn
    ]
    due.sort(key=lambda event: (event.trigger_turn, event.scheduled_id))
    return due


def mark_scheduled_event_fired(
    state: StoryState,
    scheduled_id: str,
) -> bool:
    """Mark a scheduled event as fired. Return True if found."""
    for event in state.scheduled_events:
        if event.scheduled_id == scheduled_id and not event.fired:
            event.fired = True
            state.updated_at = utc_now()
            return True
    return False


def apply_event_consequence(
    state: StoryState,
    event: Event,
    current_turn: int,
) -> None:
    """Apply structured event consequence to state in a deterministic way."""
    consequence = event.consequence
    if consequence is None:
        return

    if consequence.move_to_location_id:
        transition_location(
            state,
            to_location=consequence.move_to_location_id,
            cause=f"event:{event.event_id}",
            turn_number=current_turn,
        )

    if consequence.advance_to_stage:
        advance_scenario(state, consequence.advance_to_stage, current_turn)

    changed_flags = False
    for flag_name, flag_value in consequence.set_arc_flags.items():
        if state.scenario_position.arc_flags.get(flag_name) != flag_value:
            state.scenario_position.arc_flags[flag_name] = flag_value
            changed_flags = True
    if changed_flags:
        state.updated_at = utc_now()

    if consequence.schedule_event_type and consequence.schedule_delay_turns is not None:
        payload: dict[str, str | int | bool] = {"source_event_type": event.event_type}
        if event.location_id:
            payload["location_id"] = event.location_id
        if event.next_location_id:
            payload["next_location_id"] = event.next_location_id
        schedule_event(
            state=state,
            event_type=consequence.schedule_event_type,
            trigger_turn=current_turn + consequence.schedule_delay_turns,
            source_event_id=event.event_id,
            source="event_consequence",
            payload=payload,
        )


def _scheduled_event_id(
    event_type: str,
    trigger_turn: int,
    source_event_id: str | None,
) -> str:
    digest = hashlib.sha1(
        f"{event_type}|{trigger_turn}|{source_event_id or ''}".encode("utf-8")
    ).hexdigest()[:12]
    return f"scheduled_{digest}"
