from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from story_forge.models import (
    ActiveEvent,
    ArisRuntimeState,
    Archetype,
    BoardInstallRecord,
    BoardRuntimeState,
    CharacterGenerationContract,
    CanonEntry,
    CanonMode,
    CharacterState,
    Directive,
    DirectiveType,
    Ending,
    Event,
    EventConsequence,
    ImagePrompt,
    MemoryEntry,
    LocationTransition,
    OutputPackage,
    PermanenceLevel,
    Presentation,
    PlayerState,
    ScheduledEvent,
    ScenarioPosition,
    Scene,
    StoryState,
    SystemRuntimeState,
    WorldState,
    utc_now,
)
from story_forge.visual_artifact_schema import PendingVisualContext, VisualMemoryState


def save_story_state(path: str | Path, state: StoryState) -> Path:
    target = Path(path)
    target.write_text(json.dumps(to_primitive(state), indent=2), encoding="utf-8")
    return target


def load_story_state(path: str | Path) -> StoryState:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return story_state_from_dict(data)


def to_primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: to_primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, list):
        return [to_primitive(item) for item in value]
    if isinstance(value, dict):
        return {key: to_primitive(item) for key, item in value.items()}
    return value


def story_state_from_dict(data: dict[str, Any]) -> StoryState:
    return StoryState(
        session_id=data["session_id"],
        player_id=data["player_id"],
        engine_version=data["engine_version"],
        runtime_mode=data.get("runtime_mode", "story_forge"),
        world_pack_id=data.get("world_pack_id"),
        canon_mode=CanonMode(data.get("canon_mode", CanonMode.FIXED.value)),
        player_state=_player_state_from_dict(data.get("player_state", {})),
        world_state=_world_state_from_dict(data.get("world_state", {})),
        characters={
            character_id: _character_from_dict(character)
            for character_id, character in data.get("characters", {}).items()
        },
        memory_board=[_memory_from_dict(entry) for entry in data.get("memory_board", [])],
        canon_ledger=[_canon_from_dict(entry) for entry in data.get("canon_ledger", [])],
        directives=[_directive_from_dict(entry) for entry in data.get("directives", [])],
        recent_events=[_event_from_dict(entry) for entry in data.get("recent_events", [])],
        active_archetype=_archetype_from_dict(data.get("active_archetype")),
        installed_boards={
            board_id: _board_install_record_from_dict(board)
            for board_id, board in data.get("installed_boards", {}).items()
        },
        board_runtime=_board_runtime_state_from_dict(data.get("board_runtime", {})),
        system_state=_system_runtime_state_from_dict(data.get("system_state", {})),
        last_scene=_scene_from_dict(data.get("last_scene")),
        current_ending=_ending_from_dict(data.get("current_ending")),
        turn_count=int(data.get("turn_count", 0)),
        progress=int(data.get("progress", 0)),
        ending_scores={key: float(value) for key, value in data.get("ending_scores", {}).items()}
        or {
            "morality": 0.0,
            "power": 0.0,
            "relationships": 0.0,
            "world_impact": 0.0,
            "tension_resolution": 0.0,
        },
        aris_runtime=_aris_runtime_from_dict(data.get("aris_runtime", {})),
        llm_history=[dict(entry) for entry in data.get("llm_history", [])],
        runtime_lanes=_runtime_lanes_from_dict(data.get("runtime_lanes", {})),
        visual_memory=_visual_memory_from_dict(data.get("visual_memory", {})),
        scenario_position=_scenario_position_from_dict(data.get("scenario_position", {})),
        location_history=[
            _location_transition_from_dict(entry)
            for entry in data.get("location_history", [])
        ],
        active_events=[_active_event_from_dict(entry) for entry in data.get("active_events", [])],
        scheduled_events=[
            _scheduled_event_from_dict(entry)
            for entry in data.get("scheduled_events", [])
        ],
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        event_trace=list(data.get("event_trace", [])),
        decision_trace=list(data.get("decision_trace", [])),
    )


def output_package_from_dict(data: dict[str, Any]) -> OutputPackage:
    return OutputPackage(
        scene=_scene_from_dict(data["scene"]),
        world_update=dict(data.get("world_update", {})),
        memory_update=[_memory_from_dict(entry) for entry in data.get("memory_update", [])],
        canon_update=[_canon_from_dict(entry) for entry in data.get("canon_update", [])],
        image_prompt=_image_prompt_from_dict(data.get("image_prompt")),
        ending=_ending_from_dict(data.get("ending")),
        ending_flag=bool(data.get("ending_flag", False)),
        state_summary=dict(data.get("state_summary", {})),
        reasoning_trace=list(data.get("reasoning_trace", [])),
        presentation=_presentation_from_dict(data.get("presentation")),
    )


def _world_state_from_dict(data: dict[str, Any]) -> WorldState:
    return WorldState(
        locations=dict(data.get("locations", {})),
        factions=dict(data.get("factions", {})),
        environment_flags=list(data.get("environment_flags", [])),
        world_events=list(data.get("world_events", [])),
        timeline_marker=int(data.get("timeline_marker", 0)),
    )


def _runtime_lanes_from_dict(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict):
        return {}
    runtime_lanes: dict[str, dict[str, Any]] = {}
    for lane_id, lane_state in data.items():
        if not isinstance(lane_state, dict):
            continue
        runtime_lanes[str(lane_id)] = dict(lane_state)
    if "movie" not in runtime_lanes and "movie_renderer" in runtime_lanes:
        legacy = dict(runtime_lanes.pop("movie_renderer"))
        runtime_lanes["movie"] = {
            "lastRenderId": str(
                legacy.get("lastRenderId")
                or legacy.get("renderId")
                or ""
            ).strip(),
            "sourceLaneReference": str(
                legacy.get("sourceLaneReference")
                or "lane.text_to_3d_world"
            ).strip(),
            "timestamp": str(
                legacy.get("timestamp")
                or legacy.get("updatedAt")
                or ""
            ).strip(),
            "outputPath": str(
                legacy.get("outputPath")
                or legacy.get("outputDir")
                or ""
            ).strip(),
            "auditPath": str(
                legacy.get("auditPath")
                or ""
            ).strip(),
            "auditWitness": str(
                legacy.get("auditWitness")
                or ""
            ).strip(),
            "renderParams": {
                "title": str(legacy.get("title", "")).strip(),
                "requestedTitle": str(legacy.get("requestedTitle", "")).strip(),
                "sceneCount": int(legacy.get("sceneCount", 0) or 0),
                "videoPath": str(legacy.get("videoPath", "")).strip(),
                "screenplayPath": str(legacy.get("screenplayPath", "")).strip(),
                "shotListPath": str(legacy.get("shotListPath", "")).strip(),
                "metadataPath": str(legacy.get("metadataPath", "")).strip(),
                "framesDir": str(legacy.get("framesDir", "")).strip(),
            },
        }
    return runtime_lanes


def _player_state_from_dict(data: dict[str, Any]) -> PlayerState:
    return PlayerState(
        current_location_id=data.get("current_location_id", "story_hub"),
        inventory=list(data.get("inventory", [])),
        flags={key: bool(value) for key, value in data.get("flags", {}).items()},
        status={key: int(value) for key, value in data.get("status", {}).items()}
        or {"health": 100, "morality": 0, "power": 0},
    )


def _canon_from_dict(data: dict[str, Any]) -> CanonEntry:
    return CanonEntry(
        entry_id=data["entry_id"],
        entry_type=data["entry_type"],
        subject_id=data["subject_id"],
        description=data["description"],
        permanence_level=PermanenceLevel(data["permanence_level"]),
        timestamp=data.get("timestamp"),
        retracted=bool(data.get("retracted", False)),
        notes=data.get("notes", ""),
    )


def _memory_from_dict(data: dict[str, Any]) -> MemoryEntry:
    return MemoryEntry(
        entry_id=data["entry_id"],
        memory_type=data["memory_type"],
        weight=float(data["weight"]),
        emotional_tag=data["emotional_tag"],
        related_characters=list(data.get("related_characters", [])),
        timestamp=data.get("timestamp"),
        summary=data.get("summary", ""),
    )


def _character_from_dict(data: dict[str, Any]) -> CharacterState:
    return CharacterState(
        character_id=data["character_id"],
        name=data["name"],
        traits=list(data.get("traits", [])),
        emotional_state=data.get("emotional_state", "steady"),
        relationships=dict(data.get("relationships", {})),
        loyalty=int(data.get("loyalty", 50)),
        fear=int(data.get("fear", 10)),
        desire=int(data.get("desire", 50)),
        stability=int(data.get("stability", 100)),
        alive=bool(data.get("alive", True)),
    )


def _directive_from_dict(data: dict[str, Any]) -> Directive:
    return Directive(
        directive_id=data["directive_id"],
        kind=DirectiveType(data["kind"]),
        title=data["title"],
        description=data["description"],
        conditions=dict(data.get("conditions", {})),
        payload=dict(data.get("payload", {})),
        enabled=bool(data.get("enabled", True)),
        consumed=bool(data.get("consumed", False)),
    )


def _event_from_dict(data: dict[str, Any]) -> Event:
    return Event(
        event_id=data["event_id"],
        event_type=data["event_type"],
        participants=list(data.get("participants", [])),
        outcome=data["outcome"],
        impact_level=int(data["impact_level"]),
        timestamp=data.get("timestamp"),
        tags=list(data.get("tags", [])),
        source_directive_id=data.get("source_directive_id"),
        location_id=data.get("location_id"),
        next_location_id=data.get("next_location_id"),
        consequence=_event_consequence_from_dict(data.get("consequence")),
    )


def _archetype_from_dict(data: dict[str, Any] | None) -> Archetype | None:
    if not data:
        return None
    return Archetype(
        archetype_type=data["archetype_type"],
        variant_id=data.get("variant_id", "default"),
        variant_name=data.get("variant_name", ""),
        source_intent=data.get("source_intent", ""),
        intent_signature=data.get("intent_signature", ""),
        modifiers={key: float(value) for key, value in data.get("modifiers", {}).items()},
        character_contract=_character_generation_contract_from_dict(data.get("character_contract")),
    )


def _character_generation_contract_from_dict(
    data: dict[str, Any] | None,
) -> CharacterGenerationContract | None:
    if not data:
        return None
    return CharacterGenerationContract(
        base_archetype=data.get("base_archetype", ""),
        variant_id=data.get("variant_id", "default"),
        variant_name=data.get("variant_name", ""),
        world_pack_id=data.get("world_pack_id"),
        summary=data.get("summary", ""),
        core_drive=data.get("core_drive", ""),
        trait_pool=list(data.get("trait_pool", [])),
        role_biases=list(data.get("role_biases", [])),
        stat_biases={key: int(value) for key, value in data.get("stat_biases", {}).items()},
    )


def _board_install_record_from_dict(data: dict[str, Any]) -> BoardInstallRecord:
    return BoardInstallRecord(
        board_id=data.get("board_id", ""),
        pack_id=data.get("pack_id", ""),
        title=data.get("title", ""),
        category=data.get("category", "narrative"),
        required_modules=list(data.get("required_modules", [])),
        optional_modules=list(data.get("optional_modules", [])),
        installed_at=data.get("installed_at") or utc_now(),
        version=data.get("version", "1.0"),
    )


def _board_runtime_state_from_dict(data: dict[str, Any]) -> BoardRuntimeState:
    return BoardRuntimeState(
        installed_board_ids=list(data.get("installed_board_ids", [])),
        mounted_board_id=data.get("mounted_board_id"),
        active_board_id=data.get("active_board_id"),
        install_log=list(data.get("install_log", [])),
        swap_count=int(data.get("swap_count", 0)),
    )


def _system_runtime_state_from_dict(data: dict[str, Any]) -> SystemRuntimeState:
    return SystemRuntimeState(
        active_system=data.get("active_system", "narrative"),
        secondary_system=data.get("secondary_system"),
        collision_mode=bool(data.get("collision_mode", False)),
        medium_discipline=bool(data.get("medium_discipline", True)),
        last_collision_signature=data.get("last_collision_signature", ""),
        primary_action_id=data.get("primary_action_id"),
        support_action_ids=list(data.get("support_action_ids", [])),
        decision_trace=list(data.get("decision_trace", [])),
    )


def _scenario_position_from_dict(data: dict[str, Any]) -> ScenarioPosition:
    return ScenarioPosition(
        current_arc=data.get("current_arc", "default"),
        current_stage=data.get("current_stage", "opening"),
        entered_stage_turn=int(data.get("entered_stage_turn", 0)),
        stage_turn_count=int(data.get("stage_turn_count", 0)),
        arc_flags={key: bool(value) for key, value in data.get("arc_flags", {}).items()},
    )


def _location_transition_from_dict(data: dict[str, Any]) -> LocationTransition:
    return LocationTransition(
        from_location=data.get("from_location", ""),
        to_location=data.get("to_location", ""),
        turn_number=int(data.get("turn_number", 0)),
        cause=data.get("cause", ""),
    )


def _active_event_from_dict(data: dict[str, Any]) -> ActiveEvent:
    return ActiveEvent(
        event_id=data["event_id"],
        event_type=data["event_type"],
        started_turn=int(data.get("started_turn", 0)),
        expires_turn=(
            int(data["expires_turn"])
            if data.get("expires_turn") is not None
            else None
        ),
        resolved=bool(data.get("resolved", False)),
        source=data.get("source", "system"),
        payload=dict(data.get("payload", {})),
    )


def _event_consequence_from_dict(data: dict[str, Any] | None) -> EventConsequence | None:
    if not data:
        return None
    return EventConsequence(
        move_to_location_id=data.get("move_to_location_id"),
        schedule_event_type=data.get("schedule_event_type"),
        schedule_delay_turns=(
            int(data["schedule_delay_turns"])
            if data.get("schedule_delay_turns") is not None
            else None
        ),
        advance_to_stage=data.get("advance_to_stage"),
        set_arc_flags={key: bool(value) for key, value in data.get("set_arc_flags", {}).items()},
    )


def _scheduled_event_from_dict(data: dict[str, Any]) -> ScheduledEvent:
    return ScheduledEvent(
        scheduled_id=data["scheduled_id"],
        event_type=data["event_type"],
        trigger_turn=int(data.get("trigger_turn", 0)),
        source_event_id=data.get("source_event_id"),
        source=data.get("source", "system"),
        payload=dict(data.get("payload", {})),
        fired=bool(data.get("fired", False)),
    )


def _image_prompt_from_dict(data: dict[str, Any] | None) -> ImagePrompt | None:
    if not data:
        return None
    return ImagePrompt(
        subject=data["subject"],
        environment=data["environment"],
        action=data["action"],
        mood=data["mood"],
        symbols=list(data.get("symbols", [])),
        continuity_hooks=list(data.get("continuity_hooks", [])),
        recall_artifact_ids=list(data.get("recall_artifact_ids", [])),
        recall_context=data.get("recall_context", ""),
        tone_profile=data.get("tone_profile", ""),
        artifact_id=data.get("artifact_id", ""),
    )


def _scene_from_dict(data: dict[str, Any] | None) -> Scene | None:
    if not data:
        return None
    return Scene(
        text=data["text"],
        characters=list(data.get("characters", [])),
        choices=list(data.get("choices", [])),
        tone=data["tone"],
        consequence_tags=list(data.get("consequence_tags", [])),
    )


def _ending_from_dict(data: dict[str, Any] | None) -> Ending | None:
    if not data:
        return None
    return Ending(
        ending_type=data["ending_type"],
        summary=data["summary"],
        score_breakdown={key: float(value) for key, value in data.get("score_breakdown", {}).items()},
    )


def _presentation_from_dict(data: dict[str, Any] | None) -> Presentation | None:
    if not data:
        return None
    return Presentation(
        mode=data["mode"],
        provider=data["provider"],
        text=data["text"],
        approved=bool(data.get("approved", False)),
        degraded=bool(data.get("degraded", False)),
        audit=list(data.get("audit", [])),
    )


def _aris_runtime_from_dict(data: dict[str, Any]) -> ArisRuntimeState:
    governed_memory = {
        str(layer): [dict(entry) for entry in entries]
        for layer, entries in (data.get("governed_memory", {}) or {}).items()
    }
    return ArisRuntimeState(
        runtime_version=data.get("runtime_version", "aris-story-v1"),
        active=bool(data.get("active", True)),
        governed_memory=governed_memory or ArisRuntimeState().governed_memory,
        law_bindings=[dict(entry) for entry in data.get("law_bindings", [])],
        governance_history=[dict(entry) for entry in data.get("governance_history", [])],
        integrity=dict(data.get("integrity", {})) or ArisRuntimeState().integrity,
        kill_switch=dict(data.get("kill_switch", {})) or ArisRuntimeState().kill_switch,
        logbook=[dict(entry) for entry in data.get("logbook", [])],
    )


def _visual_memory_from_dict(data: dict[str, Any]) -> VisualMemoryState:
    pending_raw = data.get("pending_context")
    pending = None
    if isinstance(pending_raw, dict) and pending_raw:
        pending = PendingVisualContext(
            artifact_ids=list(pending_raw.get("artifact_ids", [])),
            continuity_hooks=list(pending_raw.get("continuity_hooks", [])),
            symbols=list(pending_raw.get("symbols", [])),
            match_reasons=list(pending_raw.get("match_reasons", [])),
            context=str(pending_raw.get("context", "")),
            narrative_arc=str(pending_raw.get("narrative_arc", "")),
            location=str(pending_raw.get("location", "")),
            character_ids=list(pending_raw.get("character_ids", [])),
            updated_at=str(pending_raw.get("updated_at", "")),
        )
    return VisualMemoryState(
        artifact_ids=list(data.get("artifact_ids", [])),
        hook_state={str(key): str(value) for key, value in data.get("hook_state", {}).items()},
        pending_context=pending,
        last_recall_artifact_ids=list(data.get("last_recall_artifact_ids", [])),
    )
