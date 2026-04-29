from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from story_forge.models import Event, StoryRequest, StoryState, make_id, utc_now
from story_forge.worldpacks import get_world_pack


TURN_ROUTER_LANE_ID = "narrative_router"

CATEGORY_SCENE_ADVANCEMENT = "scene_advancement"
CATEGORY_PLAYER_CHOICE = "player_choice_input"
CATEGORY_CONTEXT_GATHERING = "context_gathering"
CATEGORY_NARRATIVE_REFLECTION = "narrative_reflection"
CATEGORY_CHARACTER_ACTION = "character_action"
CATEGORY_DIALOGUE = "dialogue"
CATEGORY_WORLD_BUILDING = "world_building"
CATEGORY_STATE_UPDATE = "state_update"
CATEGORY_CONFLICT_TENSION = "conflict_tension"
CATEGORY_RESOLUTION = "resolution"
CATEGORY_DIRECTIVE_HOLD = "directive_hold"
CATEGORY_CORRECTION_RETCON = "correction_retcon"
CATEGORY_SYSTEM_META_CONTROL = "system_meta_control"
CATEGORY_CREATIVE_EXPANSION = "creative_expansion"
CATEGORY_TERMINATION_EXIT = "termination_exit"

TURN_CATEGORY_DEFINITIONS: dict[str, dict[str, object]] = {
    CATEGORY_SCENE_ADVANCEMENT: {
        "label": "Scene Advancement",
        "description": "Move the story forward. New events happen.",
        "mutates_story": True,
    },
    CATEGORY_PLAYER_CHOICE: {
        "label": "Player Choice / Input",
        "description": "User is selecting, deciding, or steering direction.",
        "mutates_story": True,
    },
    CATEGORY_CONTEXT_GATHERING: {
        "label": "Context Gathering",
        "description": "Pause story to gather who, where, and what is happening.",
        "mutates_story": False,
    },
    CATEGORY_NARRATIVE_REFLECTION: {
        "label": "Narrative Reflection",
        "description": "Summarize or restate the current situation.",
        "mutates_story": False,
    },
    CATEGORY_CHARACTER_ACTION: {
        "label": "Character Action",
        "description": "A character performs a defined action.",
        "mutates_story": True,
    },
    CATEGORY_DIALOGUE: {
        "label": "Dialogue",
        "description": "Conversation between characters.",
        "mutates_story": True,
    },
    CATEGORY_WORLD_BUILDING: {
        "label": "World Building",
        "description": "Expand lore, setting, or background.",
        "mutates_story": False,
    },
    CATEGORY_STATE_UPDATE: {
        "label": "State Update",
        "description": "Change location, inventory, relationships, or flags.",
        "mutates_story": True,
    },
    CATEGORY_CONFLICT_TENSION: {
        "label": "Conflict / Tension",
        "description": "Introduce pressure, stakes, or danger.",
        "mutates_story": True,
    },
    CATEGORY_RESOLUTION: {
        "label": "Resolution",
        "description": "Resolve an event or conflict.",
        "mutates_story": True,
    },
    CATEGORY_DIRECTIVE_HOLD: {
        "label": "Directive Hold",
        "description": "Pause progression intentionally.",
        "mutates_story": True,
    },
    CATEGORY_CORRECTION_RETCON: {
        "label": "Correction / Retcon",
        "description": "Fix inconsistency or rewrite part of the narrative.",
        "mutates_story": False,
    },
    CATEGORY_SYSTEM_META_CONTROL: {
        "label": "System / Meta Control",
        "description": "Engine rules, modes, debug, doctrine, and control.",
        "mutates_story": False,
    },
    CATEGORY_CREATIVE_EXPANSION: {
        "label": "Creative Expansion",
        "description": "Branching ideas, alternate paths, and stylistic variation.",
        "mutates_story": False,
    },
    CATEGORY_TERMINATION_EXIT: {
        "label": "Termination / Exit",
        "description": "End scene, session, or loop.",
        "mutates_story": False,
    },
}

UTILITY_CATEGORIES = {
    CATEGORY_CONTEXT_GATHERING,
    CATEGORY_NARRATIVE_REFLECTION,
    CATEGORY_WORLD_BUILDING,
    CATEGORY_CORRECTION_RETCON,
    CATEGORY_SYSTEM_META_CONTROL,
    CATEGORY_CREATIVE_EXPANSION,
    CATEGORY_TERMINATION_EXIT,
}
MUTATING_CATEGORIES = {
    category
    for category, definition in TURN_CATEGORY_DEFINITIONS.items()
    if bool(definition["mutates_story"])
}

_CONTEXT_PATTERNS = (
    "who is",
    "where am i",
    "where are we",
    "what is happening",
    "what's happening",
    "what happened",
    "what's going on",
    "current situation",
    "current status",
    "give me context",
    "inventory",
    "relationship",
    "flags",
)
_REFLECTION_PATTERNS = (
    "summarize",
    "summary",
    "recap",
    "restate",
    "reflect",
    "remind me",
)
_WORLD_PATTERNS = (
    "lore",
    "worldbuilding",
    "world building",
    "history of",
    "tell me about the world",
    "setting",
    "myth",
    "background",
)
_HOLD_PATTERNS = (
    "wait",
    "hold",
    "pause",
    "observe",
    "watch",
    "listen",
    "stay still",
)
_CORRECTION_PATTERNS = (
    "retcon",
    "correct that",
    "fix that",
    "rewrite that",
    "undo that",
    "that is inconsistent",
)
_SYSTEM_PATTERNS = (
    "engine",
    "runtime",
    "aris",
    "system",
    "meta",
    "debug",
    "seam",
    "router",
    "routing",
    "governance",
    "doctrine",
)
_CREATIVE_PATTERNS = (
    "what if",
    "alternate path",
    "alternate route",
    "branch",
    "brainstorm",
    "idea",
    "variant",
    "style it",
)
_TERMINATION_PATTERNS = (
    "end scene",
    "end session",
    "end the loop",
    "exit loop",
    "terminate",
    "stop now",
)
_DIALOGUE_PATTERNS = (
    "say",
    "ask",
    "tell",
    "reply",
    "answer",
    "speak",
    "whisper",
    "shout",
    "confess",
    "threaten",
    "demand",
    "accuse",
    "bargain",
)
_STATE_PATTERNS = (
    "take ",
    "drop ",
    "equip ",
    "inventory",
    "flag ",
    "mark ",
    "move to",
    "go to",
    "travel to",
    "relationship",
    "trust ",
    "fear ",
)
_CONFLICT_PATTERNS = (
    "attack",
    "fight",
    "threaten",
    "escalate",
    "confront",
    "danger",
    "risk",
    "pressure",
    "knife",
)
_RESOLUTION_PATTERNS = (
    "resolve",
    "settle",
    "finish this",
    "close this",
    "end the conflict",
    "repair",
    "make peace",
)
_ADVANCEMENT_PATTERNS = (
    "continue",
    "advance",
    "go forward",
    "proceed",
    "move on",
    "next",
    "deeper",
)
_ACTION_VERBS = (
    "open",
    "take",
    "move",
    "follow",
    "touch",
    "use",
    "cut",
    "carry",
    "hide",
    "approach",
    "inspect",
    "enter",
    "leave",
    "mark",
    "climb",
    "search",
    "knock",
    "steal",
    "pay",
)


@dataclass(slots=True)
class RouterEmotionSignal:
    tag: str
    intensity: int
    music_directive: str
    sources: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "intensity": self.intensity,
            "music_directive": self.music_directive,
            "sources": list(self.sources),
        }


@dataclass(slots=True)
class TurnCategoryDecision:
    requested_category: str
    resolved_category: str
    route: str
    mutation_flag: str = "mutating"
    dialogue_effect: str | None = None
    reasons: list[str] = field(default_factory=list)
    anti_loop_rules_fired: list[str] = field(default_factory=list)
    forced: bool = False
    forced_transition: bool = False
    injected_conflict: bool = False
    state_change_required: bool = False
    router_emotion: RouterEmotionSignal | None = None

    def to_payload(self) -> dict[str, Any]:
        definition = TURN_CATEGORY_DEFINITIONS[self.resolved_category]
        requested_definition = TURN_CATEGORY_DEFINITIONS[self.requested_category]
        return {
            "requested": self.requested_category,
            "requested_label": requested_definition["label"],
            "resolved": self.resolved_category,
            "resolved_label": definition["label"],
            "route": self.route,
            "mutation_flag": self.mutation_flag,
            "dialogue_effect": self.dialogue_effect,
            "anti_loop_rules_fired": list(self.anti_loop_rules_fired),
            "forced": self.forced,
            "forced_transition": self.forced_transition,
            "injected_conflict": self.injected_conflict,
            "state_change_required": self.state_change_required,
            "router_emotion": (
                self.router_emotion.to_payload() if self.router_emotion is not None else None
            ),
            "reasons": list(self.reasons),
        }


def classify_turn_category(state: StoryState, request: StoryRequest) -> TurnCategoryDecision:
    lowered = request.player_input.strip().lower()
    requested = _determine_requested_category(state, lowered, request)
    decision = TurnCategoryDecision(
        requested_category=requested,
        resolved_category=requested,
        route="story" if requested in MUTATING_CATEGORIES else "utility",
        mutation_flag="mutating" if requested in MUTATING_CATEGORIES else "non_mutating",
        reasons=[f"classified as {requested} from input heuristics"],
    )

    history = turn_router_history(state)
    if requested == CATEGORY_PLAYER_CHOICE:
        decision.resolved_category = _resolve_player_choice_followthrough(request.player_input)
        decision.route = "story"
        decision.mutation_flag = "mutating"
        decision.state_change_required = True
        decision.reasons.append(
            "player choice routed into story followthrough per narrative-physics law"
        )
    elif requested == CATEGORY_DIALOGUE:
        decision.dialogue_effect = _resolve_dialogue_effect(lowered)
        if decision.dialogue_effect == "inert":
            decision.mutation_flag = "non_mutating"
        else:
            decision.mutation_flag = "mutating"
            decision.state_change_required = True
        decision.reasons.append(
            f"dialogue effect resolved deterministically as {decision.dialogue_effect}"
        )

    if requested == CATEGORY_NARRATIVE_REFLECTION and _last_resolved_category(history) == CATEGORY_NARRATIVE_REFLECTION:
        decision.resolved_category = CATEGORY_SCENE_ADVANCEMENT
        decision.route = "story"
        decision.mutation_flag = "mutating"
        decision.forced = True
        decision.forced_transition = True
        decision.state_change_required = True
        decision.anti_loop_rules_fired.append("reflection_repeat_forced_advancement")
        decision.reasons.append("reflection cannot follow reflection; forced forward motion")

    if requested == CATEGORY_CONTEXT_GATHERING and _consecutive_count(history, CATEGORY_CONTEXT_GATHERING) >= 2:
        decision.resolved_category = CATEGORY_SCENE_ADVANCEMENT
        decision.route = "story"
        decision.mutation_flag = "mutating"
        decision.forced = True
        decision.forced_transition = True
        decision.state_change_required = True
        decision.anti_loop_rules_fired.append("context_repeat_forced_advancement")
        decision.reasons.append("context gathering cannot repeat beyond two turns; forced forward motion")

    if requested == CATEGORY_DIRECTIVE_HOLD and _last_resolved_category(history) == CATEGORY_DIRECTIVE_HOLD:
        decision.resolved_category = CATEGORY_SCENE_ADVANCEMENT
        decision.route = "story"
        decision.mutation_flag = "mutating"
        decision.forced = True
        decision.forced_transition = True
        decision.state_change_required = True
        decision.anti_loop_rules_fired.append("directive_hold_repeat_forced_advancement")
        decision.reasons.append("directive hold must resolve within one turn; forced forward motion")

    stalled_turns = int(turn_router_state(state).get("stalled_story_turns", 0))
    if stalled_turns >= 2 and decision.route == "story":
        decision.injected_conflict = True
        decision.anti_loop_rules_fired.append("stalled_story_turns_conflict_injection")
        decision.reasons.append("no meaningful state change for two story turns; inject conflict")

    if decision.resolved_category == CATEGORY_SCENE_ADVANCEMENT:
        decision.state_change_required = True

    decision.router_emotion = _derive_router_emotion(state, decision, lowered)
    return decision


def state_change_signature(state: StoryState) -> str:
    payload = {
        "location": state.player_state.current_location_id,
        "inventory": list(state.player_state.inventory),
        "player_flags": dict(sorted(state.player_state.flags.items())),
        "player_status": dict(sorted(state.player_state.status.items())),
        "environment_flags": sorted(
            flag
            for flag in state.world_state.environment_flags
            if not str(flag).startswith("stage_entry_pending_")
            and not str(flag).startswith("pending_once_")
        ),
        "relationships": sorted(
            (
                character.character_id,
                int(character.relationships.get("player", 0)),
                character.loyalty,
                character.fear,
                character.stability,
            )
            for character in state.characters.values()
        ),
        "scenario": {
            "arc": state.scenario_position.current_arc,
            "stage": state.scenario_position.current_stage,
            "flags": dict(sorted(state.scenario_position.arc_flags.items())),
        },
        "ending_scores": dict(sorted((key, float(value)) for key, value in state.ending_scores.items())),
    }
    return json.dumps(payload, sort_keys=True)


def record_turn_category(
    state: StoryState,
    request: StoryRequest,
    decision: TurnCategoryDecision,
    *,
    story_mutated: bool,
    state_changed: bool,
) -> None:
    router = turn_router_state(state)
    history = list(router.get("history", []))
    history.append(
        {
            "timestamp": utc_now(),
            "turn_count": state.turn_count,
            "raw_input": request.player_input,
            "requested": decision.requested_category,
            "resolved": decision.resolved_category,
            "route": decision.route,
            "forced": decision.forced,
            "mutation_flag": decision.mutation_flag,
            "dialogue_effect": decision.dialogue_effect,
            "forced_transition": decision.forced_transition,
            "injected_conflict": decision.injected_conflict,
            "anti_loop_rules_fired": list(decision.anti_loop_rules_fired),
            "story_mutated": story_mutated,
            "state_changed": state_changed,
            "router_emotion": (
                decision.router_emotion.to_payload()
                if decision.router_emotion is not None
                else None
            ),
        }
    )
    history = history[-24:]
    stalled_story_turns = int(router.get("stalled_story_turns", 0))
    if decision.route == "story" and story_mutated:
        stalled_story_turns = 0 if state_changed else stalled_story_turns + 1

    state.runtime_lanes[TURN_ROUTER_LANE_ID] = {
        "history": history,
        "last_state_signature": state_change_signature(state),
        "stalled_story_turns": stalled_story_turns,
        "last_requested_category": decision.requested_category,
        "last_resolved_category": decision.resolved_category,
        "updatedAt": utc_now(),
    }


def turn_router_state(state: StoryState) -> dict[str, Any]:
    lane = state.runtime_lanes.get(TURN_ROUTER_LANE_ID, {})
    if not isinstance(lane, dict):
        return {}
    return lane


def turn_router_history(state: StoryState) -> list[dict[str, Any]]:
    history = turn_router_state(state).get("history", [])
    if not isinstance(history, list):
        return []
    return [entry for entry in history if isinstance(entry, dict)]


def build_conflict_injection_event(
    state: StoryState,
    decision: TurnCategoryDecision,
) -> Event:
    location = state.player_state.current_location_id or "unknown"
    return Event(
        event_id=make_id("event"),
        event_type="conflict",
        participants=["player"],
        outcome=(
            f"Stalled pressure breaks at {location}, forcing the story out of repetition."
        ),
        impact_level=3,
        tags=["router_injected_conflict", decision.resolved_category],
        location_id=location,
    )


def build_turn_category_summary(state: StoryState) -> dict[str, Any]:
    router = turn_router_state(state)
    history = turn_router_history(state)
    return {
        "stalled_story_turns": int(router.get("stalled_story_turns", 0)),
        "last_requested_category": router.get("last_requested_category"),
        "last_resolved_category": router.get("last_resolved_category"),
        "last_router_emotion": (
            history[-1].get("router_emotion") if history else None
        ),
        "history": history[-6:],
    }


def _determine_requested_category(
    state: StoryState,
    lowered: str,
    request: StoryRequest,
) -> str:
    normalized = _normalize_phrase(lowered)
    if request.metadata.get("from_scene_choice"):
        return CATEGORY_PLAYER_CHOICE
    if _matches_current_scene_choice(state, normalized):
        return CATEGORY_PLAYER_CHOICE
    if _contains_pattern(lowered, _TERMINATION_PATTERNS):
        return CATEGORY_TERMINATION_EXIT
    if lowered.startswith("/"):
        return CATEGORY_SYSTEM_META_CONTROL
    if _matches_authored_story_prompt(state, normalized):
        if _looks_like_defined_action(normalized):
            return CATEGORY_CHARACTER_ACTION
        return CATEGORY_SCENE_ADVANCEMENT
    if _contains_pattern(lowered, _CORRECTION_PATTERNS):
        return CATEGORY_CORRECTION_RETCON
    if _contains_pattern(lowered, _SYSTEM_PATTERNS):
        return CATEGORY_SYSTEM_META_CONTROL
    if _contains_pattern(lowered, _WORLD_PATTERNS):
        return CATEGORY_WORLD_BUILDING
    if _contains_pattern(lowered, _CREATIVE_PATTERNS):
        return CATEGORY_CREATIVE_EXPANSION
    if _contains_pattern(lowered, _CONTEXT_PATTERNS) or (
        lowered.endswith("?") and any(token in lowered for token in ("who", "where", "what"))
    ):
        return CATEGORY_CONTEXT_GATHERING
    if _contains_pattern(lowered, _REFLECTION_PATTERNS):
        return CATEGORY_NARRATIVE_REFLECTION
    if _contains_pattern(lowered, _HOLD_PATTERNS):
        return CATEGORY_DIRECTIVE_HOLD
    if lowered.startswith('"') or _contains_pattern(lowered, _DIALOGUE_PATTERNS):
        return CATEGORY_DIALOGUE
    if _contains_pattern(lowered, _RESOLUTION_PATTERNS):
        return CATEGORY_RESOLUTION
    if _contains_pattern(lowered, _CONFLICT_PATTERNS):
        return CATEGORY_CONFLICT_TENSION
    if _contains_pattern(lowered, _STATE_PATTERNS):
        return CATEGORY_STATE_UPDATE
    if _contains_pattern(lowered, _ADVANCEMENT_PATTERNS):
        return CATEGORY_SCENE_ADVANCEMENT
    if _looks_like_defined_action(lowered):
        return CATEGORY_CHARACTER_ACTION
    return CATEGORY_SCENE_ADVANCEMENT


def _resolve_player_choice_followthrough(text: str) -> str:
    lowered = text.strip().lower()
    if _looks_like_defined_action(lowered):
        return CATEGORY_CHARACTER_ACTION
    return CATEGORY_SCENE_ADVANCEMENT


def _last_resolved_category(history: list[dict[str, Any]]) -> str | None:
    if not history:
        return None
    return str(history[-1].get("resolved", "") or "") or None


def _consecutive_count(history: list[dict[str, Any]], category: str) -> int:
    count = 0
    for entry in reversed(history):
        if entry.get("resolved") != category:
            break
        count += 1
    return count


def _contains_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    return any(
        re.search(rf"(^|[^a-z0-9]){re.escape(pattern)}($|[^a-z0-9])", text)
        for pattern in patterns
    )


def _looks_like_defined_action(lowered: str) -> bool:
    if lowered.startswith(("i ", "we ")):
        return True
    first_word = re.split(r"\s+", lowered.strip(), maxsplit=1)[0]
    return first_word in _ACTION_VERBS


def _resolve_dialogue_effect(lowered: str) -> str:
    informational_patterns = (
        "confess",
        "reveal",
        "admit",
        "warn",
        "answer",
        "name the truth",
        "tell the truth",
        "explain",
        "remember",
    )
    relational_patterns = (
        "promise",
        "apologize",
        "forgive",
        "swear",
        "pledge",
        "ally",
        "trust",
    )
    pressure_patterns = (
        "threaten",
        "demand",
        "accuse",
        "ultimatum",
        "bargain",
        "coerce",
        "pressure",
    )
    if _contains_pattern(lowered, informational_patterns):
        return "informational"
    if _contains_pattern(lowered, relational_patterns):
        return "relational"
    if _contains_pattern(lowered, pressure_patterns):
        return "pressure"
    return "inert"


def _ordered_unique(values: list[str | None]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _derive_router_emotion(
    state: StoryState,
    decision: TurnCategoryDecision,
    lowered: str,
) -> RouterEmotionSignal:
    sources: list[str] = ["router_category"]
    stalled_turns = int(turn_router_state(state).get("stalled_story_turns", 0) or 0)
    recent_events = list(state.recent_events[-3:])
    scene_tone = str(getattr(state.last_scene, "tone", "") or "").lower()
    event_types = {str(event.event_type or "").lower() for event in recent_events}

    if decision.injected_conflict or decision.resolved_category == CATEGORY_CONFLICT_TENSION:
        tag = "pressure"
        music_directive = "pulse"
    elif decision.dialogue_effect == "pressure":
        tag = "pressure"
        music_directive = "pulse"
    elif decision.resolved_category == CATEGORY_RESOLUTION:
        tag = "release"
        music_directive = "resolve"
    elif decision.dialogue_effect == "relational":
        tag = "bond"
        music_directive = "weave"
    elif decision.resolved_category == CATEGORY_NARRATIVE_REFLECTION:
        tag = "brooding"
        music_directive = "drone"
    elif decision.resolved_category == CATEGORY_CONTEXT_GATHERING:
        tag = "clarity"
        music_directive = "hold"
    elif (
        "eerie" in scene_tone
        or "uneasy" in scene_tone
        or event_types.intersection({"omens", "overlap", "uncanny_manifestation", "ritual_memory"})
    ):
        tag = "dread"
        music_directive = "drone"
        sources.append("scene_state")
    elif decision.resolved_category == CATEGORY_WORLD_BUILDING:
        tag = "wonder"
        music_directive = "glow"
    else:
        tag = "focus"
        music_directive = "carry"

    if any(word in lowered for word in ("fear", "dread", "wrong", "haunt")):
        tag = "dread"
        music_directive = "drone"
        sources.append("input_language")

    intensity = 1
    if stalled_turns >= 1:
        intensity += 1
        sources.append("stalled_story_turns")
    if decision.forced_transition or decision.injected_conflict:
        intensity += 1
        sources.append("anti_loop")
    if any(int(getattr(event, "impact_level", 0) or 0) >= 4 for event in recent_events):
        intensity += 1
        sources.append("recent_event_impact")

    return RouterEmotionSignal(
        tag=tag,
        intensity=max(1, min(3, intensity)),
        music_directive=music_directive,
        sources=_ordered_unique(sources),
    )


def _normalize_phrase(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r"[.!?,;:\"'()\[\]{}]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _matches_current_scene_choice(state: StoryState, normalized: str) -> bool:
    if not normalized or state.last_scene is None:
        return False
    return any(
        _normalize_phrase(choice) == normalized
        for choice in state.last_scene.choices
    )


def _matches_authored_story_prompt(state: StoryState, normalized: str) -> bool:
    if not normalized or state.world_pack_id is None:
        return False
    try:
        world_pack = get_world_pack(state.world_pack_id)
    except Exception:
        return False
    return any(
        _normalize_phrase(keyword) == normalized
        for template in world_pack.event_templates
        for keyword in template.required_keywords
    )
