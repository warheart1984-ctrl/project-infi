from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from story_forge.visual_artifact_schema import VisualMemoryState


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


ARIS_MEMORY_LAYERS = (
    "foundational",
    "operational",
    "learned_patterns",
    "rejected_patterns",
    "archive",
)

PRESENTATION_MODES = (
    "present",
    "explain",
    "narrate",
    "stability",
    "degraded",
)

RUNTIME_MODES = (
    "story_forge",
    "strict",
)


def default_aris_governed_memory() -> dict[str, list[dict[str, Any]]]:
    return {layer: [] for layer in ARIS_MEMORY_LAYERS}


def default_aris_integrity() -> dict[str, Any]:
    return {
        "ok": True,
        "initialized": False,
        "profile_mode": "story_forge",
        "verified_at": "",
        "protected_paths": [],
        "required_paths": [],
        "optional_paths": [],
        "baseline_hashes": {},
        "current_hashes": {},
        "changed": [],
        "soft_changed": [],
        "removed": [],
        "soft_removed": [],
        "missing": [],
        "optional_missing": [],
    }


def default_aris_kill_switch() -> dict[str, Any]:
    return {
        "mode": "nominal",
        "active": False,
        "reason": "",
        "summary": "ARIS runtime nominal.",
        "triggered_at": "",
        "requires_manual_reset": False,
        "diagnostics": {},
        "recent_events": [],
    }


class CanonMode(str, Enum):
    FIXED = "fixed"
    FLEXIBLE = "flexible"
    FRACTURED = "fractured"
    PLAYER_DRIVEN = "player_driven"


class DirectiveType(str, Enum):
    SOFT = "soft"
    HARD = "hard"
    ESCALATION = "escalation"
    END = "end"
    ONE_TIME = "one_time"


class PermanenceLevel(str, Enum):
    TRANSIENT = "transient"
    STABLE = "stable"
    ABSOLUTE = "absolute"


@dataclass(slots=True)
class StoryRequest:
    player_id: str
    player_input: str
    session_id: str | None = None
    choice_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Directive:
    directive_id: str
    kind: DirectiveType
    title: str
    description: str
    conditions: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    consumed: bool = False


@dataclass(slots=True)
class DirectiveAction:
    directive_id: str
    effect: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorldState:
    locations: dict[str, dict[str, Any]] = field(default_factory=dict)
    factions: dict[str, dict[str, Any]] = field(default_factory=dict)
    environment_flags: list[str] = field(default_factory=list)
    world_events: list[str] = field(default_factory=list)
    timeline_marker: int = 0


@dataclass(slots=True)
class CanonEntry:
    entry_id: str
    entry_type: str
    subject_id: str
    description: str
    permanence_level: PermanenceLevel
    timestamp: str = field(default_factory=utc_now)
    retracted: bool = False
    notes: str = ""


@dataclass(slots=True)
class MemoryEntry:
    entry_id: str
    memory_type: str
    weight: float
    emotional_tag: str
    related_characters: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now)
    summary: str = ""


@dataclass(slots=True)
class CharacterState:
    character_id: str
    name: str
    traits: list[str] = field(default_factory=list)
    emotional_state: str = "steady"
    relationships: dict[str, int] = field(default_factory=dict)
    loyalty: int = 50
    fear: int = 10
    desire: int = 50
    stability: int = 100
    alive: bool = True


@dataclass(slots=True)
class PlayerState:
    current_location_id: str = "story_hub"
    inventory: list[str] = field(default_factory=list)
    flags: dict[str, bool] = field(default_factory=dict)
    status: dict[str, int] = field(
        default_factory=lambda: {
            "health": 100,
            "morality": 0,
            "power": 0,
        }
    )


@dataclass(slots=True)
class Event:
    event_id: str
    event_type: str
    participants: list[str]
    outcome: str
    impact_level: int
    timestamp: str = field(default_factory=utc_now)
    tags: list[str] = field(default_factory=list)
    source_directive_id: str | None = None
    location_id: str | None = None
    next_location_id: str | None = None
    consequence: EventConsequence | None = None


@dataclass(slots=True)
class CharacterGenerationContract:
    base_archetype: str
    variant_id: str
    variant_name: str
    world_pack_id: str | None = None
    summary: str = ""
    core_drive: str = ""
    trait_pool: list[str] = field(default_factory=list)
    role_biases: list[str] = field(default_factory=list)
    stat_biases: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class BoardInstallRecord:
    board_id: str
    pack_id: str
    title: str
    category: str
    required_modules: list[str] = field(default_factory=list)
    optional_modules: list[str] = field(default_factory=list)
    installed_at: str = field(default_factory=utc_now)
    version: str = "1.0"


@dataclass(slots=True)
class BoardRuntimeState:
    installed_board_ids: list[str] = field(default_factory=list)
    mounted_board_id: str | None = None
    active_board_id: str | None = None
    install_log: list[str] = field(default_factory=list)
    swap_count: int = 0


@dataclass(slots=True)
class SystemRuntimeState:
    active_system: str = "narrative"
    secondary_system: str | None = None
    collision_mode: bool = False
    medium_discipline: bool = True
    last_collision_signature: str = ""
    primary_action_id: str | None = None
    support_action_ids: list[str] = field(default_factory=list)
    decision_trace: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Archetype:
    archetype_type: str
    variant_id: str = "default"
    variant_name: str = ""
    source_intent: str = ""
    intent_signature: str = ""
    modifiers: dict[str, float] = field(default_factory=dict)
    character_contract: CharacterGenerationContract | None = None


@dataclass(slots=True)
class ScenarioPosition:
    current_arc: str = "default"
    current_stage: str = "opening"
    entered_stage_turn: int = 0
    stage_turn_count: int = 0
    arc_flags: dict[str, bool] = field(default_factory=dict)


@dataclass(slots=True)
class LocationTransition:
    from_location: str
    to_location: str
    turn_number: int
    cause: str


@dataclass(slots=True)
class ActiveEvent:
    event_id: str
    event_type: str
    started_turn: int
    expires_turn: int | None = None
    resolved: bool = False
    source: str = "system"
    payload: dict[str, str | int | bool] = field(default_factory=dict)


@dataclass(slots=True)
class EventConsequence:
    move_to_location_id: str | None = None
    schedule_event_type: str | None = None
    schedule_delay_turns: int | None = None
    advance_to_stage: str | None = None
    set_arc_flags: dict[str, bool] = field(default_factory=dict)


@dataclass(slots=True)
class ScheduledEvent:
    scheduled_id: str
    event_type: str
    trigger_turn: int
    source_event_id: str | None = None
    source: str = "system"
    payload: dict[str, str | int | bool] = field(default_factory=dict)
    fired: bool = False


@dataclass(slots=True)
class ImagePrompt:
    subject: str
    environment: str
    action: str
    mood: str
    symbols: list[str] = field(default_factory=list)
    continuity_hooks: list[str] = field(default_factory=list)
    recall_artifact_ids: list[str] = field(default_factory=list)
    recall_context: str = ""
    tone_profile: str = ""
    artifact_id: str = ""


@dataclass(slots=True)
class Scene:
    text: str
    characters: list[str]
    choices: list[str]
    tone: str
    consequence_tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Presentation:
    mode: str
    provider: str
    text: str
    approved: bool
    degraded: bool = False
    audit: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Ending:
    ending_type: str
    summary: str
    score_breakdown: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class StateSnapshot:
    world_state: WorldState
    characters: list[CharacterState]
    memory_entries: list[MemoryEntry]
    canon_entries: list[CanonEntry]
    active_directives: list[Directive]


@dataclass(slots=True)
class OutputPackage:
    scene: Scene
    world_update: dict[str, Any]
    memory_update: list[MemoryEntry]
    canon_update: list[CanonEntry]
    image_prompt: ImagePrompt | None
    ending: Ending | None
    ending_flag: bool
    state_summary: dict[str, Any]
    reasoning_trace: list[str] = field(default_factory=list)
    presentation: Presentation | None = None


@dataclass(slots=True)
class DirectivePassResult:
    actions: list[DirectiveAction] = field(default_factory=list)
    forced_events: list[Event] = field(default_factory=list)


@dataclass(slots=True)
class ArisRuntimeState:
    runtime_version: str = "aris-story-v1"
    active: bool = True
    governed_memory: dict[str, list[dict[str, Any]]] = field(default_factory=default_aris_governed_memory)
    law_bindings: list[dict[str, Any]] = field(default_factory=list)
    governance_history: list[dict[str, Any]] = field(default_factory=list)
    integrity: dict[str, Any] = field(default_factory=default_aris_integrity)
    kill_switch: dict[str, Any] = field(default_factory=default_aris_kill_switch)
    logbook: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class StoryState:
    session_id: str
    player_id: str
    engine_version: str
    runtime_mode: str = "story_forge"
    world_pack_id: str | None = None
    canon_mode: CanonMode = CanonMode.FIXED
    player_state: PlayerState = field(default_factory=PlayerState)
    world_state: WorldState = field(default_factory=WorldState)
    characters: dict[str, CharacterState] = field(default_factory=dict)
    memory_board: list[MemoryEntry] = field(default_factory=list)
    canon_ledger: list[CanonEntry] = field(default_factory=list)
    directives: list[Directive] = field(default_factory=list)
    recent_events: list[Event] = field(default_factory=list)
    active_archetype: Archetype | None = None
    installed_boards: dict[str, BoardInstallRecord] = field(default_factory=dict)
    board_runtime: BoardRuntimeState = field(default_factory=BoardRuntimeState)
    system_state: SystemRuntimeState = field(default_factory=SystemRuntimeState)
    last_scene: Scene | None = None
    current_ending: Ending | None = None
    turn_count: int = 0
    progress: int = 0
    ending_scores: dict[str, float] = field(
        default_factory=lambda: {
            "morality": 0.0,
            "power": 0.0,
            "relationships": 0.0,
            "world_impact": 0.0,
            "tension_resolution": 0.0,
        }
    )
    aris_runtime: ArisRuntimeState = field(default_factory=ArisRuntimeState)
    llm_history: list[dict[str, Any]] = field(default_factory=list)
    runtime_lanes: dict[str, dict[str, Any]] = field(default_factory=dict)
    visual_memory: VisualMemoryState = field(default_factory=VisualMemoryState)
    scenario_position: ScenarioPosition = field(default_factory=ScenarioPosition)
    location_history: list[LocationTransition] = field(default_factory=list)
    active_events: list[ActiveEvent] = field(default_factory=list)
    scheduled_events: list[ScheduledEvent] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    event_trace: list[str] = field(default_factory=list)
    decision_trace: list[str] = field(default_factory=list)
