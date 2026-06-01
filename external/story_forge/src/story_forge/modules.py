from __future__ import annotations

from copy import deepcopy
from typing import Any

from story_forge.archetypes import resolve_active_archetype
from story_forge.debug import build_runtime_status
from story_forge.models import (
    Archetype,
    CanonEntry,
    CanonMode,
    CharacterState,
    DirectiveAction,
    DirectivePassResult,
    DirectiveType,
    Ending,
    Event,
    ImagePrompt,
    MemoryEntry,
    OutputPackage,
    PermanenceLevel,
    Scene,
    StateSnapshot,
    StoryRequest,
    StoryState,
    WorldState,
    make_id,
)


def build_state_snapshot(state: StoryState) -> StateSnapshot:
    return StateSnapshot(
        world_state=deepcopy(state.world_state),
        characters=[deepcopy(character) for character in state.characters.values()],
        memory_entries=[deepcopy(entry) for entry in state.memory_board],
        canon_entries=[deepcopy(entry) for entry in state.canon_ledger if not entry.retracted],
        active_directives=[
            deepcopy(directive)
            for directive in state.directives
            if directive.enabled and not directive.consumed
        ],
    )


def run_directives(state: StoryState, snapshot: StateSnapshot) -> DirectivePassResult:
    result = DirectivePassResult()
    world_flags = set(snapshot.world_state.environment_flags)
    memory_tags = {entry.memory_type for entry in snapshot.memory_entries}

    for directive in state.directives:
        if not directive.enabled or directive.consumed:
            continue
        conditions = directive.conditions
        if state.turn_count < conditions.get("turn_at_least", 0):
            continue
        required_flags = set(conditions.get("world_flags_any", []))
        if required_flags and not (required_flags & world_flags):
            continue
        required_memory = set(conditions.get("required_memory_tags", []))
        if required_memory and not (required_memory & memory_tags):
            continue

        result.actions.append(
            DirectiveAction(
                directive_id=directive.directive_id,
                effect=directive.title,
                payload=deepcopy(directive.payload),
            )
        )

        force_event_type = directive.payload.get("force_event_type")
        if force_event_type:
            result.forced_events.append(
                Event(
                    event_id=make_id("event"),
                    event_type=force_event_type,
                    participants=list(directive.payload.get("participants", [])),
                    outcome=directive.payload.get("outcome", directive.description),
                    impact_level=int(directive.payload.get("impact_level", 3)),
                    tags=list(directive.payload.get("tags", [])),
                    source_directive_id=directive.directive_id,
                )
            )

        if directive.kind == DirectiveType.ONE_TIME:
            directive.consumed = True
            directive.enabled = False

    return result


def resolve_events(
    request: StoryRequest,
    snapshot: StateSnapshot,
    forced_events: list[Event],
) -> list[Event]:
    events = list(forced_events)
    message = request.player_input.strip()
    lowered = message.lower()
    participants = _detect_participants(message, snapshot)
    if not participants:
        participants = ["player"]

    event_type = "choice"
    impact = 2
    tags = ["choice"]
    outcome = f"The player chooses: {message}"
    category = str(request.metadata.get("turn_category_resolved", "") or "").strip()

    if category == "scene_advancement":
        event_type = "advancement"
        impact = 3
        tags = ["advancement", "forward_motion"]
        outcome = f"The stalled scene moves forward: {message}"
    elif category == "character_action":
        event_type = "action"
        impact = 3
        tags = ["action", "defined_move"]
        outcome = f"A defined character action changes the scene: {message}"
    elif category == "dialogue":
        event_type = "dialogue"
        impact = 2
        tags = ["dialogue", "exchange"]
        outcome = f"Conversation reshapes the next beat: {message}"
    elif category == "state_update":
        event_type = "state_update"
        impact = 3
        tags = ["state_change", "internal_shift"]
        outcome = f"Internal story state changes through the action: {message}"
    elif category == "conflict_tension":
        event_type = "battle"
        impact = 4
        tags = ["conflict", "pressure"]
        outcome = f"Pressure and danger escalate through the action: {message}"
    elif category == "resolution":
        event_type = "resolution"
        impact = 4
        tags = ["resolution", "closure"]
        outcome = f"The action pushes the current conflict toward resolution: {message}"

    if any(keyword in lowered for keyword in ("ally", "help", "join", "protect", "trust")):
        event_type = "alliance"
        impact = 3
        tags = ["bond", "trust"]
        outcome = f"An alliance deepens after the player action: {message}"
    elif any(keyword in lowered for keyword in ("betray", "lie", "steal", "abandon")):
        event_type = "betrayal"
        impact = 4
        tags = ["rupture", "betrayal"]
        outcome = f"The action introduces betrayal into the story: {message}"
    elif any(keyword in lowered for keyword in ("attack", "fight", "kill", "war")):
        event_type = "battle"
        impact = 5
        tags = ["conflict", "danger"]
        outcome = f"Violence reshapes the scene: {message}"
    elif any(keyword in lowered for keyword in ("discover", "learn", "reveal", "remember")):
        event_type = "discovery"
        impact = 3
        tags = ["revelation", "knowledge"]
        outcome = f"A revelation changes the world state: {message}"
    elif any(keyword in lowered for keyword in ("survive", "revive", "return to life")):
        event_type = "revival"
        impact = 4
        tags = ["revival", "contradiction"]
        primary = participants[0]
        outcome = f"{primary} returns from the brink, challenging established truth."
    elif any(keyword in lowered for keyword in ("travel", "go", "move", "journey")):
        event_type = "travel"
        impact = 2
        tags = ["movement"]
        outcome = f"The story shifts location through the player's action: {message}"
    elif any(keyword in lowered for keyword in ("end", "final", "finish", "resolve")):
        event_type = "resolution"
        impact = 4
        tags = ["ending", "resolution"]
        outcome = f"The player pushes the story toward an ending: {message}"

    if "kill" in lowered and participants:
        primary = participants[0]
        event_type = "death"
        outcome = f"{primary} is slain as the story turns darker."
        tags = ["death", "irreversible"]

    events.append(
        Event(
            event_id=make_id("event"),
            event_type=event_type,
            participants=participants,
            outcome=outcome,
            impact_level=impact,
            tags=tags,
        )
    )
    return events


def update_world_state(
    state: StoryState,
    events: list[Event],
    actions: list[DirectiveAction],
) -> tuple[WorldState, dict[str, Any]]:
    world = deepcopy(state.world_state)
    added_flags: set[str] = set()

    for event in events:
        world.timeline_marker += 1
        world.world_events.append(event.outcome)
        if event.event_type in {"battle", "death", "betrayal", "conflict"}:
            added_flags.add("unrest")
        if event.event_type in {"discovery", "resolution"}:
            added_flags.add("insight")
        if event.event_type == "travel":
            added_flags.add("displacement")

    for action in actions:
        for flag in action.payload.get("world_flags_add", []):
            added_flags.add(str(flag))
        for location, details in action.payload.get("locations_update", {}).items():
            existing = world.locations.get(location, {})
            existing.update(details)
            world.locations[location] = existing

    existing_flags = set(world.environment_flags)
    world.environment_flags = sorted(existing_flags | added_flags)
    summary = {
        "timeline_marker": world.timeline_marker,
        "flags": list(world.environment_flags),
        "recent_world_events": world.world_events[-3:],
    }
    return world, summary


def update_memory_board(
    state: StoryState,
    request: StoryRequest,
    events: list[Event],
) -> tuple[list[MemoryEntry], list[MemoryEntry]]:
    board = deepcopy(state.memory_board)
    new_entries: list[MemoryEntry] = []

    for existing in board:
        existing.weight = round(max(0.1, existing.weight * 0.98), 3)

    for event in events:
        summary = event.outcome if len(event.outcome) < 180 else f"{event.outcome[:177]}..."
        weight = min(1.0, 0.2 + (event.impact_level * 0.15))
        if sum(1 for entry in board if entry.memory_type == event.event_type) >= 1:
            weight = min(1.0, weight + 0.15)
        emotional_tag = _emotion_for_event(event.event_type)
        entry = MemoryEntry(
            entry_id=make_id("memory"),
            memory_type=event.event_type,
            weight=round(weight, 3),
            emotional_tag=emotional_tag,
            related_characters=[p for p in event.participants if p != "player"],
            summary=summary,
        )
        board.append(entry)
        new_entries.append(entry)

    if any(keyword in request.player_input.lower() for keyword in ("always", "never", "promise")):
        preference_entry = MemoryEntry(
            entry_id=make_id("memory"),
            memory_type="vow",
            weight=0.8,
            emotional_tag="resolve",
            related_characters=[],
            summary=f"Player vow: {request.player_input[:160]}",
        )
        board.append(preference_entry)
        new_entries.append(preference_entry)

    board.sort(key=lambda entry: entry.weight, reverse=True)
    board = board[:50]
    return board, new_entries


def update_canon_ledger(
    state: StoryState,
    events: list[Event],
    actions: list[DirectiveAction],
) -> tuple[list[CanonEntry], list[CanonEntry]]:
    ledger = deepcopy(state.canon_ledger)
    additions: list[CanonEntry] = []

    for event in events:
        if event.impact_level < 3 and event.event_type not in {"death", "resolution"}:
            continue
        subject_id = event.participants[0] if event.participants else "world"
        entry = CanonEntry(
            entry_id=make_id("canon"),
            entry_type=event.event_type,
            subject_id=subject_id,
            description=event.outcome,
            permanence_level=_permanence_for_event(event.event_type, event.impact_level),
            notes="from directive" if event.source_directive_id else "",
        )
        if _apply_canon_entry(ledger, state.canon_mode, entry, allow_player_override=True):
            additions.append(entry)

    for action in actions:
        if not action.payload.get("canon_note"):
            continue
        entry = CanonEntry(
            entry_id=make_id("canon"),
            entry_type="directive",
            subject_id=action.directive_id,
            description=str(action.payload["canon_note"]),
            permanence_level=PermanenceLevel.STABLE,
            notes="directive note",
        )
        if _apply_canon_entry(ledger, state.canon_mode, entry, allow_player_override=False):
            additions.append(entry)

    return ledger, additions


def update_character_states(
    state: StoryState,
    events: list[Event],
    memory_board: list[MemoryEntry],
    world_state: WorldState,
) -> dict[str, CharacterState]:
    characters = deepcopy(state.characters)

    for event in events:
        for participant in [p for p in event.participants if p != "player"]:
            character = characters.get(participant)
            if character is None:
                character = CharacterState(character_id=participant, name=participant.title())
                characters[participant] = character
            _apply_event_to_character(character, event)

    if "unrest" in world_state.environment_flags:
        for character in characters.values():
            character.fear = min(100, character.fear + 1)
            character.stability = max(0, character.stability - 1)

    for memory in memory_board[:8]:
        for character_id in memory.related_characters:
            character = characters.get(character_id)
            if not character:
                continue
            if memory.memory_type == "betrayal":
                character.relationships["player"] = character.relationships.get("player", 0) - 4
            if memory.memory_type == "alliance":
                character.relationships["player"] = character.relationships.get("player", 0) + 4

    return characters


def assign_archetype(
    memory_board: list[MemoryEntry],
    player_intent: str = "",
    world_pack_id: str | None = None,
    decision_trace: list[str] | None = None,
) -> Archetype:
    return resolve_active_archetype(
        memory_board=memory_board,
        player_intent=player_intent,
        world_pack_id=world_pack_id,
        decision_trace=decision_trace or [],
    )


def generate_scene(
    snapshot: StateSnapshot,
    recent_events: list[Event],
    archetype: Archetype | None,
) -> Scene:
    tone = _tone_from_snapshot(snapshot, recent_events)
    featured: list[str] = []
    if recent_events:
        participant_ids = [
            participant
            for participant in recent_events[-1].participants
            if participant != "player"
        ]
        for participant_id in participant_ids:
            character = next(
                (item for item in snapshot.characters if item.character_id == participant_id),
                None,
            )
            if character is not None:
                featured.append(character.name)
    if not featured:
        featured = [character.name for character in snapshot.characters[:3]]
    if not featured:
        featured = ["The player"]

    recent = recent_events[-1] if recent_events else None
    hook = recent.outcome if recent else "The world waits for the next turning point."
    flags = ", ".join(snapshot.world_state.environment_flags) or "quiet tension"
    archetype_line = (
        f"{archetype.archetype_type} / {archetype.variant_name}"
        if archetype and archetype.variant_name
        else (archetype.archetype_type if archetype else "undefined")
    )

    text = (
        f"{hook} The atmosphere carries {flags}. "
        f"The story leans into a {tone} cadence, shaped by a {archetype_line} player archetype. "
        f"Present in the scene: {', '.join(featured)}."
    )
    choices = _choices_for_tone(tone, featured[0])
    consequence_tags = sorted(
        {tag for event in recent_events[-3:] for tag in event.tags}
        | {directive.kind.value for directive in snapshot.active_directives}
    )
    return Scene(
        text=text,
        characters=featured,
        choices=choices,
        tone=tone,
        consequence_tags=consequence_tags,
    )


def resolve_ending(
    state: StoryState,
    actions: list[DirectiveAction],
) -> Ending | None:
    memory_pressure = round(sum(entry.weight for entry in state.memory_board[:10]), 3)
    instability = round(
        sum(max(0, 100 - character.stability) for character in state.characters.values()) / 100,
        3,
    ) if state.characters else 0.0
    directive_pressure = round(float(len(actions)) * 0.4, 3)
    score = round(memory_pressure + instability + directive_pressure + (state.progress * 0.2), 3)

    should_end = any(action.payload.get("end_now") for action in actions)
    should_end = should_end or state.progress >= 6
    should_end = should_end or "ending_ready" in state.world_state.environment_flags
    if not should_end:
        return None

    if instability >= 1.2:
        ending_type = "cataclysm"
        summary = "The world fractures under accumulated instability and unresolved wounds."
    elif memory_pressure >= 2.5:
        ending_type = "legacy"
        summary = "Long memory crystallizes into a final reckoning that honors every consequence."
    else:
        ending_type = "convergence"
        summary = "Threads converge into a deliberate ending shaped by choice and pressure."

    return Ending(
        ending_type=ending_type,
        summary=summary,
        score_breakdown={
            "memory_pressure": memory_pressure,
            "instability": instability,
            "directive_pressure": directive_pressure,
            "total": score,
        },
    )


def package_output(
    state: StoryState,
    scene: Scene,
    world_update: dict[str, Any],
    memory_update: list[MemoryEntry],
    canon_update: list[CanonEntry],
    image_prompt: ImagePrompt | None,
    ending: Ending | None,
    reasoning_trace: list[str],
) -> OutputPackage:
    return OutputPackage(
        scene=scene,
        world_update=world_update,
        memory_update=memory_update,
        canon_update=canon_update,
        image_prompt=image_prompt,
        ending=ending,
        ending_flag=ending is not None,
        state_summary={
            "session_id": state.session_id,
            "world_pack_id": state.world_pack_id,
            "runtime_mode": state.runtime_mode,
            "turn_count": state.turn_count,
            "progress": state.progress,
            "canon_mode": state.canon_mode.value,
            "current_location_id": state.player_state.current_location_id,
            "current_arc": state.scenario_position.current_arc,
            "current_stage": state.scenario_position.current_stage,
            "stage_turn_count": state.scenario_position.stage_turn_count,
            "arc_flags": dict(state.scenario_position.arc_flags),
            "timeline_marker": state.world_state.timeline_marker,
            "memory_entries": len(state.memory_board),
            "canon_entries": len([entry for entry in state.canon_ledger if not entry.retracted]),
            "characters": len(state.characters),
            "active_events": len([event for event in state.active_events if not event.resolved]),
            "scheduled_events": len([event for event in state.scheduled_events if not event.fired]),
            "location_history_entries": len(state.location_history),
            "archetype": state.active_archetype.archetype_type if state.active_archetype else None,
            "archetype_variant": state.active_archetype.variant_id if state.active_archetype else None,
            "archetype_signature": state.active_archetype.intent_signature if state.active_archetype else None,
            "ending_scores": dict(state.ending_scores),
            "presentation_hooks": [],
            "runtime_status": build_runtime_status(state),
        },
        reasoning_trace=reasoning_trace,
    )


def _detect_participants(message: str, snapshot: StateSnapshot) -> list[str]:
    lowered = message.lower()
    found: list[str] = []
    for character in snapshot.characters:
        aliases = {
            character.character_id.lower(),
            character.character_id.lower().replace("_", " "),
            character.name.lower(),
        }
        aliases.update(part for part in character.character_id.lower().split("_") if len(part) >= 3)
        aliases.update(part for part in character.name.lower().split() if len(part) >= 3)
        if any(alias in lowered for alias in aliases):
            found.append(character.character_id)
    return found


def _emotion_for_event(event_type: str) -> str:
    mapping = {
        "action": "resolve",
        "advancement": "anticipation",
        "alliance": "hope",
        "betrayal": "hurt",
        "battle": "fear",
        "conflict": "fear",
        "death": "grief",
        "discovery": "wonder",
        "dialogue": "curiosity",
        "resolution": "resolve",
        "state_update": "anticipation",
        "travel": "anticipation",
    }
    return mapping.get(event_type, "curiosity")


def _permanence_for_event(event_type: str, impact_level: int) -> PermanenceLevel:
    if event_type in {"death", "resolution"} or impact_level >= 5:
        return PermanenceLevel.ABSOLUTE
    if impact_level >= 3:
        return PermanenceLevel.STABLE
    return PermanenceLevel.TRANSIENT


def _apply_canon_entry(
    ledger: list[CanonEntry],
    canon_mode: CanonMode,
    new_entry: CanonEntry,
    allow_player_override: bool,
) -> bool:
    conflicts = [
        entry
        for entry in ledger
        if not entry.retracted
        and entry.subject_id == new_entry.subject_id
        and (
            (
                entry.entry_type == new_entry.entry_type
                and entry.description != new_entry.description
            )
            or ({entry.entry_type, new_entry.entry_type} == {"death", "revival"})
        )
    ]
    if not conflicts:
        ledger.append(new_entry)
        return True

    if canon_mode == CanonMode.FIXED:
        return False
    if canon_mode == CanonMode.FLEXIBLE:
        for conflict in conflicts:
            conflict.retracted = True
            conflict.notes = "retracted by flexible canon update"
        ledger.append(new_entry)
        return True
    if canon_mode == CanonMode.FRACTURED:
        new_entry.notes = "fractured canon branch"
        ledger.append(new_entry)
        return True
    if canon_mode == CanonMode.PLAYER_DRIVEN and allow_player_override:
        for conflict in conflicts:
            conflict.retracted = True
            conflict.notes = "overridden by player-driven canon"
        ledger.append(new_entry)
        return True
    return False


def _apply_event_to_character(character: CharacterState, event: Event) -> None:
    if event.event_type == "alliance":
        character.emotional_state = "hopeful"
        character.loyalty = min(100, character.loyalty + 10)
        character.relationships["player"] = character.relationships.get("player", 0) + 8
    elif event.event_type == "betrayal":
        character.emotional_state = "wounded"
        character.loyalty = max(0, character.loyalty - 15)
        character.stability = max(0, character.stability - 10)
        character.relationships["player"] = character.relationships.get("player", 0) - 12
    elif event.event_type == "battle":
        character.emotional_state = "shaken"
        character.fear = min(100, character.fear + 15)
        character.stability = max(0, character.stability - 12)
    elif event.event_type == "death":
        character.emotional_state = "gone"
        character.alive = False
        character.stability = 0
    elif event.event_type == "discovery":
        character.emotional_state = "alert"
        character.desire = min(100, character.desire + 12)
    elif event.event_type == "travel":
        character.emotional_state = "restless"
        character.desire = min(100, character.desire + 5)
    elif event.event_type == "resolution":
        character.emotional_state = "resolved"
        character.stability = min(100, character.stability + 5)


def _tone_from_snapshot(snapshot: StateSnapshot, recent_events: list[Event]) -> str:
    if any(event.event_type in {"battle", "death"} for event in recent_events[-2:]):
        return "ominous"
    if any(event.event_type == "betrayal" for event in recent_events[-2:]):
        return "urgent"
    if any(event.event_type == "discovery" for event in recent_events[-2:]):
        return "curious"
    if any(directive.kind in {DirectiveType.HARD, DirectiveType.END} for directive in snapshot.active_directives):
        return "pressured"
    return "steady"


def _choices_for_tone(tone: str, lead_name: str) -> list[str]:
    if tone == "ominous":
        return [
            f"Shield {lead_name} from the fallout.",
            "Push deeper even if it breaks the canon balance.",
            "Retreat and preserve what remains.",
        ]
    if tone == "urgent":
        return [
            "Confront the betrayal directly.",
            "Set a trap and wait for proof.",
            "Trade trust for short-term survival.",
        ]
    if tone == "curious":
        return [
            "Follow the new clue.",
            "Question the oldest witness.",
            "Archive the discovery before acting.",
        ]
    return [
        "Advance the story with conviction.",
        "Pause and gather more context.",
        "Let the directive pressure simmer for one more turn.",
    ]
