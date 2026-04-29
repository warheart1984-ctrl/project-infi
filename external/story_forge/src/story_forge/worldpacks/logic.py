from __future__ import annotations

from copy import deepcopy
from typing import Any

from story_forge.models import (
    CanonEntry,
    CharacterState,
    Ending,
    Event,
    EventConsequence,
    MemoryEntry,
    PermanenceLevel,
    Scene,
    StoryRequest,
    StoryState,
    make_id,
    utc_now,
)
from story_forge.worldpacks.base import EventTemplate, WorldPack

STAGE_ENTRY_PENDING_PREFIX = "stage_entry_pending_"
ONE_SHOT_PENDING_PREFIX = "pending_once_"
LOOP_GUARD_LANE_ID = "narrative_loop_guard"
LOOP_GUARD_REPEAT_WINDOW = 4
LOOP_GUARD_HISTORY_LIMIT = 24


def stage_entry_pending_flag(stage: str) -> str:
    return f"{STAGE_ENTRY_PENDING_PREFIX}{str(stage or '').strip().lower()}"


def one_shot_pending_flag(name: str) -> str:
    return f"{ONE_SHOT_PENDING_PREFIX}{str(name or '').strip().lower()}"


def _is_pending_runtime_flag(flag: str) -> bool:
    normalized = str(flag or "").strip().lower()
    return normalized.startswith(STAGE_ENTRY_PENDING_PREFIX) or normalized.startswith(ONE_SHOT_PENDING_PREFIX)


def loop_guard_state(state: StoryState) -> dict[str, Any]:
    lane = state.runtime_lanes.get(LOOP_GUARD_LANE_ID, {})
    if not isinstance(lane, dict):
        return {}
    return lane


def loop_guard_summary(state: StoryState) -> dict[str, Any]:
    lane = loop_guard_state(state)
    history = lane.get("history", [])
    if not isinstance(history, list):
        history = []
    consequence_memory = _consequence_memory_entries(state)
    recent_templates = [
        str(entry.get("template_id", "")).strip()
        for entry in history[-4:]
        if isinstance(entry, dict) and str(entry.get("template_id", "")).strip()
    ]
    return {
        "repeat_pressure": int(lane.get("repeat_pressure", 0) or 0),
        "locked_signatures": len(_locked_signatures(state)),
        "exhausted_consequences": sum(
            1 for entry in consequence_memory if bool(entry.get("exhausted", False))
        ),
        "recent_consequences": [
            str(entry.get("event_tag", "")).strip()
            for entry in consequence_memory[-3:]
            if isinstance(entry, dict) and str(entry.get("event_tag", "")).strip()
        ],
        "recent_templates": recent_templates,
        "repeat_break_due": bool(state.scenario_position.arc_flags.get("repeat_break_due", False)),
        "last_escalation_stage": str(lane.get("last_escalation_stage", "") or ""),
    }


def template_loop_signature(
    state: StoryState,
    template: EventTemplate,
    *,
    current_location_id: str | None = None,
    current_stage: str | None = None,
) -> str:
    location_id = (
        current_location_id
        or state.player_state.current_location_id
        or template.location_id
        or "any"
    )
    if template.location_id != "any":
        location_id = template.location_id
    stage = current_stage or state.scenario_position.current_stage or "opening"
    arc = state.scenario_position.current_arc or state.world_pack_id or "default"
    return f"{arc}:{stage}:{location_id}:{template.template_id}"


def record_template_resolution(
    state: StoryState,
    template: EventTemplate,
) -> dict[str, Any]:
    lane = loop_guard_state(state)
    history = lane.get("history", [])
    if not isinstance(history, list):
        history = []

    signature = template_loop_signature(state, template)
    locked_signatures = _locked_signatures(state)
    consequence_memory = _consequence_memory_entries(state)
    location_id = (
        state.player_state.current_location_id
        or (template.location_id if template.location_id != "any" else "any")
    )
    prior_count = sum(
        1
        for entry in history
        if isinstance(entry, dict) and str(entry.get("signature", "")) == signature
    )

    history.append(
        {
            "signature": signature,
            "template_id": template.template_id,
            "location_id": location_id,
            "stage": state.scenario_position.current_stage,
            "impact_level": template.impact_level,
            "timestamp": utc_now(),
        }
    )
    history = history[-LOOP_GUARD_HISTORY_LIMIT:]

    locked = False
    if template.impact_level >= 4 and signature not in locked_signatures:
        locked_signatures.add(signature)
        locked = True

    repeat_pressure = int(lane.get("repeat_pressure", 0) or 0)
    escalation_armed = False
    recent_cycle_key = ""
    recent_history = history[-LOOP_GUARD_REPEAT_WINDOW:]
    current_location_repeat_count = sum(
        1
        for entry in recent_history
        if isinstance(entry, dict) and str(entry.get("location_id", "")).strip() == location_id
    )
    if len(recent_history) >= LOOP_GUARD_REPEAT_WINDOW:
        recent_signatures = [
            str(entry.get("signature", ""))
            for entry in recent_history
            if isinstance(entry, dict)
        ]
        recent_locations = [
            str(entry.get("location_id", ""))
            for entry in recent_history
            if isinstance(entry, dict)
        ]
        signature_set = {item for item in recent_signatures if item}
        location_counts = {
            item: recent_locations.count(item)
            for item in {location for location in recent_locations if location}
        }
        should_escalate = (
            len(signature_set) <= 2
            or any(count >= 3 for count in location_counts.values())
        )
        if should_escalate:
            recent_cycle_key = "|".join(recent_signatures)
            if recent_cycle_key and recent_cycle_key != str(lane.get("last_cycle_key", "")):
                repeat_pressure += 1
                escalation_armed = True
                state.scenario_position.arc_flags["repeat_pressure"] = True
                state.scenario_position.arc_flags["repeat_break_due"] = True

    exhausted = False
    if template.impact_level >= 4:
        exhausted = True
    elif prior_count > 0 and template.next_location_id is None and current_location_repeat_count >= 2:
        exhausted = True
    elif escalation_armed and template.next_location_id is None:
        exhausted = True

    if exhausted:
        locked_signatures.add(signature)
        _append_consequence_memory(
            consequence_memory,
            template=template,
            signature=signature,
            location_id=location_id,
            stage=state.scenario_position.current_stage,
            exhausted=True,
        )

    state.runtime_lanes[LOOP_GUARD_LANE_ID] = {
        "history": history,
        "repeat_pressure": repeat_pressure,
        "locked_signatures": sorted(locked_signatures),
        "consequence_memory": consequence_memory[-LOOP_GUARD_HISTORY_LIMIT:],
        "last_cycle_key": recent_cycle_key or str(lane.get("last_cycle_key", "")),
        "last_escalation_stage": (
            state.scenario_position.current_stage if escalation_armed else str(lane.get("last_escalation_stage", ""))
        ),
        "updatedAt": utc_now(),
    }
    return {
        "signature": signature,
        "repeated": prior_count > 0,
        "locked": locked,
        "exhausted": exhausted,
        "repeat_pressure": repeat_pressure,
        "escalation_armed": escalation_armed,
        "location_id": location_id,
        "template_id": template.template_id,
    }


def _locked_signatures(state: StoryState) -> set[str]:
    lane = loop_guard_state(state)
    raw = lane.get("locked_signatures", [])
    if not isinstance(raw, list):
        return set()
    return {
        str(item).strip()
        for item in raw
        if str(item).strip()
    }


def _consequence_memory_entries(state: StoryState) -> list[dict[str, Any]]:
    lane = loop_guard_state(state)
    raw = lane.get("consequence_memory", [])
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def _append_consequence_memory(
    consequence_memory: list[dict[str, Any]],
    *,
    template: EventTemplate,
    signature: str,
    location_id: str,
    stage: str,
    exhausted: bool,
) -> None:
    for entry in consequence_memory:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("meaning_signature", "")).strip() == signature:
            entry["exhausted"] = bool(exhausted or entry.get("exhausted", False))
            entry["updated_at"] = utc_now()
            return

    consequence_memory.append(
        {
            "event_tag": template.template_id,
            "event_type": template.event_type,
            "scene_id": location_id,
            "stage": stage,
            "outcome": template.summary,
            "state_effects": _template_state_effects(template),
            "meaning_signature": signature,
            "exhausted": exhausted,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
    )


def _template_state_effects(template: EventTemplate) -> list[str]:
    effects = list(template.world_flags_add)
    if template.next_location_id:
        effects.append(f"move:{template.next_location_id}")
    if template.consequence is not None:
        consequence = template.consequence
        if consequence.move_to_location_id:
            effects.append(f"move:{consequence.move_to_location_id}")
        if consequence.advance_to_stage:
            effects.append(f"stage:{consequence.advance_to_stage}")
        if consequence.schedule_event_type:
            effects.append(f"schedule:{consequence.schedule_event_type}")
        effects.extend(
            f"flag:{key}"
            for key, enabled in consequence.set_arc_flags.items()
            if enabled
        )
    return sorted({effect for effect in effects if str(effect).strip()})


def seed_state_from_world_pack(state: StoryState, world_pack: WorldPack) -> StoryState:
    state.world_pack_id = world_pack.pack_id
    state.player_state.current_location_id = world_pack.start_location_id
    state.scenario_position.current_arc = world_pack.pack_id
    state.scenario_position.current_stage = "opening"
    state.scenario_position.entered_stage_turn = state.turn_count
    state.scenario_position.stage_turn_count = 0
    state.scenario_position.arc_flags = {}
    state.system_state.active_system = (
        world_pack.systems[0].system_id if world_pack.systems else "narrative"
    )
    state.system_state.secondary_system = None
    state.system_state.collision_mode = False
    state.system_state.last_collision_signature = ""
    state.system_state.primary_action_id = None
    state.system_state.support_action_ids = []
    state.system_state.decision_trace = []
    state.world_state.locations = {
        location.location_id: {
            "name": location.name,
            "description": location.description,
            "tags": list(location.tags),
            "connections": list(location.connections),
            "discovered": location.location_id == world_pack.start_location_id,
        }
        for location in world_pack.locations
    }
    state.world_state.factions = {
        faction_id: {"description": description}
        for faction_id, description in world_pack.factions.items()
    }
    if not state.characters:
        state.characters = {
            npc.npc_id: CharacterState(
                character_id=npc.npc_id,
                name=npc.name,
                traits=list(npc.traits),
                emotional_state="watchful",
                relationships={"player": npc.relationship_to_player},
                loyalty=npc.loyalty,
                fear=npc.fear,
                desire=npc.desire,
                stability=npc.stability,
            )
            for npc in world_pack.npcs
        }
    if not state.canon_ledger:
        state.canon_ledger = [
            CanonEntry(
                entry_id=make_id("canon"),
                entry_type=anchor.entry_type,
                subject_id=anchor.subject_id,
                description=anchor.description,
                permanence_level=PermanenceLevel(anchor.permanence),
                notes="world-pack anchor",
            )
            for anchor in world_pack.canon_anchors
        ]
    state.world_state.environment_flags = sorted(
        set(state.world_state.environment_flags) | {"world_pack_loaded", world_pack.pack_id}
    )
    return state


def select_event_template(
    world_pack: WorldPack,
    state: StoryState,
    request: StoryRequest,
) -> EventTemplate | None:
    current_location = state.player_state.current_location_id or world_pack.start_location_id
    current_stage = state.scenario_position.current_stage or "opening"
    lowered = request.player_input.lower()
    from_scene_choice = bool(request.metadata.get("from_scene_choice", False))
    memory_types = {entry.memory_type for entry in state.memory_board}
    canon_types = {entry.entry_type for entry in state.canon_ledger if not entry.retracted}
    world_flags = set(state.world_state.environment_flags)
    pending_stage_flag = stage_entry_pending_flag(current_stage)
    recent_template_ids = _recent_template_ids(state)
    last_template_id = recent_template_ids[0] if recent_template_ids else None
    loop_guard = loop_guard_state(state)
    loop_history = loop_guard.get("history", [])
    if not isinstance(loop_history, list):
        loop_history = []
    recent_guard_signatures = [
        str(entry.get("signature", "")).strip()
        for entry in loop_history[-6:]
        if isinstance(entry, dict)
    ]
    recent_guard_templates = {
        str(entry.get("template_id", "")).strip()
        for entry in loop_history[-6:]
        if isinstance(entry, dict)
    }
    consequence_memory = _consequence_memory_entries(state)
    location_repeat_count = sum(
        1
        for entry in loop_history[-6:]
        if isinstance(entry, dict)
        and str(entry.get("location_id", "")).strip() == current_location
    )
    locked_signatures = _locked_signatures(state)
    raw_repeat_pressure = int(loop_guard.get("repeat_pressure", 0) or 0)
    repeat_pressure = (
        raw_repeat_pressure
        if str(loop_guard.get("last_escalation_stage", "")).strip() == current_stage
        and location_repeat_count >= 2
        else 0
    )
    focused_npcs = {
        npc.npc_id
        for npc in world_pack.npcs
        if any(alias in lowered for alias in _npc_aliases(state, npc.npc_id))
    }
    focused_locations = {
        location.location_id
        for location in world_pack.locations
        if any(alias in lowered for alias in _location_aliases(location.location_id, location.name))
    }
    has_explicit_focus = bool(focused_npcs or focused_locations)

    eligible_templates = _eligible_event_templates(
        world_pack,
        current_location=current_location,
        current_stage=current_stage,
        world_flags=world_flags,
        memory_types=memory_types,
        canon_types=canon_types,
    )

    forced_stage_templates = [
        template
        for template in eligible_templates
        if any(_is_pending_runtime_flag(flag) for flag in template.required_world_flags)
    ]
    templates_to_score = forced_stage_templates if forced_stage_templates else eligible_templates

    scored: list[tuple[int, str, EventTemplate]] = []
    for template in templates_to_score:
        signature = template_loop_signature(
            state,
            template,
            current_location_id=current_location,
            current_stage=current_stage,
        )
        if signature in locked_signatures:
            continue
        is_forced_stage_template = any(
            _is_pending_runtime_flag(flag)
            for flag in template.required_world_flags
        )

        keyword_score = 0
        for keyword in template.required_keywords:
            if keyword in lowered:
                keyword_score += 4
        participant_score = 0
        for participant in template.participants:
            aliases = _npc_aliases(state, participant)
            if any(alias in lowered for alias in aliases):
                participant_score += 3
        location_focus_score = 0
        if template.location_id != "any":
            for alias in _location_aliases(
                template.location_id,
                state.world_state.locations.get(template.location_id, {}).get("name", template.location_id),
            ):
                if alias in lowered:
                    location_focus_score += 4
                    break
        if (
            has_explicit_focus
            and not is_forced_stage_template
            and keyword_score == 0
            and participant_score == 0
            and location_focus_score == 0
        ):
            continue

        score = keyword_score + participant_score + location_focus_score + template.stage_priority
        exhausted_meaning_count = sum(
            1
            for entry in consequence_memory
            if str(entry.get("scene_id", "")).strip() == current_location
            and str(entry.get("stage", "")).strip() == current_stage
            and str(entry.get("event_tag", "")).strip() == template.template_id
            and bool(entry.get("exhausted", False))
        )
        aftermath_pressure = sum(
            1
            for entry in consequence_memory
            if str(entry.get("scene_id", "")).strip() == current_location
            and str(entry.get("stage", "")).strip() == current_stage
            and bool(entry.get("exhausted", False))
        )
        if template.location_id == current_location:
            score += 3
        if not template.required_keywords:
            score += 1
        if template.next_location_id is not None and from_scene_choice:
            score += 2
        if template.next_location_id and template.next_location_id != current_location:
            score += 2
        if any(_is_pending_runtime_flag(flag) for flag in template.required_world_flags):
            score += 12
        if template.template_id == last_template_id:
            score -= 10 if from_scene_choice else 6
        elif template.template_id in recent_template_ids:
            score -= 3
        if signature in recent_guard_signatures:
            score -= 5 + repeat_pressure
        if exhausted_meaning_count > 0:
            score -= 8 * exhausted_meaning_count
        if repeat_pressure > 0:
            if template.template_id not in recent_guard_templates:
                score += 4 + min(repeat_pressure, 3)
            if template.next_location_id and template.next_location_id != current_location:
                score += 4 + min(repeat_pressure, 2)
            if template.location_id == "any":
                score += 3
            if location_repeat_count >= 2 and template.location_id == current_location and template.next_location_id is None:
                score -= 6 + min(repeat_pressure, 3)
        if aftermath_pressure > 0 and location_repeat_count >= 2:
            if template.next_location_id and template.next_location_id != current_location:
                score += 4 + min(aftermath_pressure, 2)
            if any(_is_pending_runtime_flag(flag) for flag in template.required_world_flags):
                score += 4 + min(aftermath_pressure, 2)
            if template.location_id == "any":
                score += 2 + min(aftermath_pressure, 2)
        scored.append((score, template.template_id, template))

    scored.sort(key=lambda item: (-item[0], item[1]))
    if scored and scored[0][0] > 0:
        return scored[0][2]
    if has_explicit_focus:
        return None
    fallback = [item[2] for item in scored if item[2].location_id == current_location]
    return fallback[0] if fallback else None


def select_authored_recovery_template(
    world_pack: WorldPack,
    state: StoryState,
    request: StoryRequest,
) -> EventTemplate | None:
    current_location = state.player_state.current_location_id or world_pack.start_location_id
    current_stage = state.scenario_position.current_stage or "opening"
    lowered = request.player_input.lower()
    memory_types = {entry.memory_type for entry in state.memory_board}
    canon_types = {entry.entry_type for entry in state.canon_ledger if not entry.retracted}
    world_flags = set(state.world_state.environment_flags)
    recent_template_ids = _recent_template_ids(state, limit=4)
    loop_guard = loop_guard_state(state)
    loop_history = loop_guard.get("history", [])
    if not isinstance(loop_history, list):
        loop_history = []
    recent_guard_templates = {
        str(entry.get("template_id", "")).strip()
        for entry in loop_history[-6:]
        if isinstance(entry, dict)
    }
    consequence_memory = _consequence_memory_entries(state)
    locked_signatures = _locked_signatures(state)
    focused_npcs = {
        npc.npc_id
        for npc in world_pack.npcs
        if any(alias in lowered for alias in _npc_aliases(state, npc.npc_id))
    }
    focused_locations = {
        location.location_id
        for location in world_pack.locations
        if any(alias in lowered for alias in _location_aliases(location.location_id, location.name))
    }
    if focused_npcs or focused_locations:
        return None

    eligible_templates = _eligible_event_templates(
        world_pack,
        current_location=current_location,
        current_stage=current_stage,
        world_flags=world_flags,
        memory_types=memory_types,
        canon_types=canon_types,
    )
    if not eligible_templates:
        return None

    scored: list[tuple[int, str, EventTemplate]] = []
    for template in eligible_templates:
        signature = template_loop_signature(
            state,
            template,
            current_location_id=current_location,
            current_stage=current_stage,
        )
        if signature in locked_signatures:
            continue

        exhausted_meaning_count = sum(
            1
            for entry in consequence_memory
            if str(entry.get("scene_id", "")).strip() == current_location
            and str(entry.get("stage", "")).strip() == current_stage
            and str(entry.get("event_tag", "")).strip() == template.template_id
            and bool(entry.get("exhausted", False))
        )
        consequence_weight = 0
        if template.next_location_id and template.next_location_id != current_location:
            consequence_weight += 6
        if template.world_flags_add:
            consequence_weight += 3
        if template.consequence is not None:
            if template.consequence.move_to_location_id:
                consequence_weight += 4
            if template.consequence.advance_to_stage:
                consequence_weight += 4
            if template.consequence.schedule_event_type:
                consequence_weight += 3
            if template.consequence.set_arc_flags:
                consequence_weight += 2

        score = template.stage_priority + consequence_weight
        if template.location_id == current_location:
            score += 4
        elif template.location_id == "any":
            score += 3
        if template.impact_level >= 4:
            score += 2
        if any(_is_pending_runtime_flag(flag) for flag in template.required_world_flags):
            score += 8
        if template.template_id in recent_template_ids:
            score -= 6
        if template.template_id in recent_guard_templates:
            score -= 4
        if exhausted_meaning_count > 0:
            score -= 8 * exhausted_meaning_count

        scored.append((score, template.template_id, template))

    scored.sort(key=lambda item: (-item[0], item[1]))
    if scored and scored[0][0] > 0:
        return scored[0][2]
    return None


def _eligible_event_templates(
    world_pack: WorldPack,
    *,
    current_location: str,
    current_stage: str,
    world_flags: set[str],
    memory_types: set[str],
    canon_types: set[str],
) -> list[EventTemplate]:
    eligible_templates: list[EventTemplate] = []
    for template in world_pack.event_templates:
        if template.location_id not in {current_location, "any"}:
            continue
        if template.allowed_stages and current_stage not in template.allowed_stages:
            continue
        if template.required_world_flags and not set(template.required_world_flags).issubset(world_flags):
            continue
        if template.required_memory_types and not set(template.required_memory_types).intersection(memory_types):
            continue
        if template.required_canon_types and not set(template.required_canon_types).issubset(canon_types):
            continue
        eligible_templates.append(template)
    return eligible_templates


def _npc_aliases(state: StoryState, npc_id: str) -> set[str]:
    aliases = {npc_id.lower(), npc_id.replace("_", " ").lower()}
    character = state.characters.get(npc_id)
    if character:
        full_name = character.name.lower()
        aliases.add(full_name)
        aliases.update(part for part in full_name.split() if len(part) >= 3)
    aliases.update(part for part in npc_id.lower().split("_") if len(part) >= 3)
    return {alias for alias in aliases if alias}


def _location_aliases(location_id: str, location_name: str) -> set[str]:
    aliases = {
        str(location_id or "").lower(),
        str(location_id or "").replace("_", " ").lower(),
        str(location_name or "").lower(),
    }
    aliases.update(part for part in str(location_name or "").lower().split() if len(part) >= 4)
    aliases.update(part for part in str(location_id or "").lower().split("_") if len(part) >= 4)
    return {alias for alias in aliases if alias}


def _recent_template_ids(state: StoryState, limit: int = 3) -> list[str]:
    template_ids: list[str] = []
    for event in reversed(state.recent_events):
        for tag in event.tags:
            if tag.startswith("template:"):
                template_id = tag.split(":", 1)[1]
                if template_id and template_id not in template_ids:
                    template_ids.append(template_id)
                    break
        if len(template_ids) >= limit:
            break
    return template_ids


def event_from_template(
    template: EventTemplate,
    current_location_id: str | None = None,
) -> Event:
    canonical_location_id = current_location_id if template.location_id == "any" else template.location_id
    consequence = _consequence_from_template(template)
    tags = list(template.memory_tags)
    tags.append(f"template:{template.template_id}")
    tags.extend(f"system:{system_id}" for system_id in template.system_tags if system_id)
    return Event(
        event_id=make_id("event"),
        event_type=template.event_type,
        participants=list(template.participants),
        outcome=template.summary,
        impact_level=template.impact_level,
        tags=tags,
        location_id=canonical_location_id,
        next_location_id=template.next_location_id,
        consequence=consequence,
    )


def apply_template_to_state(
    state: StoryState,
    template: EventTemplate,
) -> None:
    for flag in template.world_flags_add:
        if flag not in state.world_state.environment_flags:
            state.world_state.environment_flags.append(flag)

    for npc_id, delta in template.relationship_deltas.items():
        character = state.characters.get(npc_id)
        if not character:
            continue
        character.relationships["player"] = character.relationships.get("player", 0) + delta

    for npc_id, delta in template.loyalty_deltas.items():
        character = state.characters.get(npc_id)
        if character:
            character.loyalty = max(0, min(100, character.loyalty + delta))

    for npc_id, delta in template.fear_deltas.items():
        character = state.characters.get(npc_id)
        if character:
            character.fear = max(0, min(100, character.fear + delta))

    for npc_id, delta in template.stability_deltas.items():
        character = state.characters.get(npc_id)
        if character:
            character.stability = max(0, min(100, character.stability + delta))

    for score_name, delta in template.score_effects.items():
        state.ending_scores[score_name] = round(state.ending_scores.get(score_name, 0.0) + delta, 3)

    pending_stage_flags = [
        flag
        for flag in template.required_world_flags
        if _is_pending_runtime_flag(flag)
    ]
    if pending_stage_flags:
        state.world_state.environment_flags = [
            flag
            for flag in state.world_state.environment_flags
            if flag not in pending_stage_flags
        ]

    if "morality" in template.score_effects:
        state.player_state.status["morality"] = int(round(state.ending_scores["morality"]))
    if "power" in template.score_effects:
        state.player_state.status["power"] = int(round(state.ending_scores["power"]))


def _consequence_from_template(template: EventTemplate) -> EventConsequence | None:
    consequence = deepcopy(template.consequence) if template.consequence is not None else None
    if template.next_location_id:
        if consequence is None:
            consequence = EventConsequence()
        if consequence.move_to_location_id is None:
            consequence.move_to_location_id = template.next_location_id
    return consequence


def build_memory_entries_from_pack(
    world_pack: WorldPack,
    state: StoryState,
    template: EventTemplate,
    request: StoryRequest,
) -> list[MemoryEntry]:
    lowered = request.player_input.lower()
    current_location = state.player_state.current_location_id
    new_entries: list[MemoryEntry] = []
    for trigger in world_pack.memory_triggers:
        if template.event_type not in trigger.event_types:
            continue
        if trigger.location_ids and "any" not in trigger.location_ids and current_location not in trigger.location_ids:
            continue
        if trigger.required_keywords and not any(keyword in lowered for keyword in trigger.required_keywords):
            continue
        summary = trigger.summary_template.format(
            title=template.title,
            location=current_location,
            player=state.player_id,
        )
        if any(entry.summary == summary for entry in state.memory_board[-6:]):
            continue
        new_entries.append(
            MemoryEntry(
                entry_id=make_id("memory"),
                memory_type=trigger.memory_type,
                weight=trigger.weight,
                emotional_tag=trigger.emotional_tag,
                related_characters=list(trigger.related_characters or template.participants),
                summary=summary,
            )
        )
    return new_entries


def build_scene_from_template(
    world_pack: WorldPack,
    state: StoryState,
    template: EventTemplate,
) -> Scene:
    location = state.world_state.locations.get(
        state.player_state.current_location_id or world_pack.start_location_id,
        {},
    )
    relationships = []
    for npc_id in template.participants:
        character = state.characters.get(npc_id)
        if character:
            relation = character.relationships.get("player", 0)
            relationships.append(f"{character.name} ({relation:+d})")

    text = (
        f"{template.scene_opening} "
        f"Current location: {location.get('name', state.player_state.current_location_id)}. "
        f"Relationship pressure: {', '.join(relationships) if relationships else 'none'}."
    )
    return Scene(
        text=text,
        characters=[state.characters[npc_id].name for npc_id in template.participants if npc_id in state.characters],
        choices=list(template.choice_texts),
        tone=world_pack.tone,
        consequence_tags=list(template.memory_tags) + list(template.system_tags),
    )


def refresh_ending_scores(state: StoryState) -> None:
    relationship_total = 0.0
    world_impact = float(len(state.world_state.environment_flags) * 3)
    tension_resolution = float(max(0, 100 - len([flag for flag in state.world_state.environment_flags if "unrest" in flag]) * 10))
    active = 0
    for character in state.characters.values():
        relationship_total += character.relationships.get("player", 0)
        active += 1
    if active:
        relationship_total = relationship_total / active

    state.ending_scores["relationships"] = round(relationship_total, 3)
    state.ending_scores["world_impact"] = round(world_impact, 3)
    state.ending_scores["tension_resolution"] = round(tension_resolution, 3)
    state.ending_scores["morality"] = float(state.player_state.status.get("morality", 0))
    state.ending_scores["power"] = float(state.player_state.status.get("power", 0))


def resolve_world_pack_ending(world_pack: WorldPack, state: StoryState) -> Ending | None:
    refresh_ending_scores(state)
    flags = set(state.world_state.environment_flags)
    memory_types = {entry.memory_type for entry in state.memory_board}
    candidates: list[tuple[int, str, Ending]] = []
    for template in world_pack.ending_templates:
        if template.required_flags and not set(template.required_flags).issubset(flags):
            continue
        if template.required_memory_types and not set(template.required_memory_types).issubset(memory_types):
            continue
        if any(
            state.characters.get(npc_id, CharacterState(character_id=npc_id, name=npc_id)).relationships.get("player", 0) < value
            for npc_id, value in template.relationship_requirements.items()
        ):
            continue
        if any(state.ending_scores.get(key, 0.0) < value for key, value in template.min_scores.items()):
            continue
        if any(state.ending_scores.get(key, 0.0) > value for key, value in template.max_scores.items()):
            continue
        score = int(sum(abs(state.ending_scores.get(key, 0.0)) for key in template.min_scores))
        candidates.append(
            (
                score,
                template.ending_id,
                Ending(
                    ending_type=template.ending_type,
                    summary=template.summary,
                    score_breakdown=deepcopy(state.ending_scores),
                ),
            )
        )

    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2] if candidates else None
