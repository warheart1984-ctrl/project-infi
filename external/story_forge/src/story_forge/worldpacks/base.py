from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from story_forge.models import EventConsequence


@dataclass(slots=True)
class LocationSeed:
    location_id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    connections: list[str] = field(default_factory=list)


@dataclass(slots=True)
class NpcSeed:
    npc_id: str
    name: str
    role: str
    home_location_id: str
    description: str
    traits: list[str] = field(default_factory=list)
    loyalty: int = 50
    fear: int = 10
    desire: int = 50
    stability: int = 100
    relationship_to_player: int = 0


@dataclass(slots=True)
class CanonAnchor:
    anchor_id: str
    entry_type: str
    subject_id: str
    description: str
    permanence: str = "absolute"


@dataclass(slots=True)
class MemoryTrigger:
    trigger_id: str
    event_types: list[str]
    required_keywords: list[str]
    location_ids: list[str]
    memory_type: str
    emotional_tag: str
    weight: float
    summary_template: str
    related_characters: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EventTemplate:
    template_id: str
    title: str
    event_type: str
    location_id: str
    summary: str
    scene_opening: str
    participants: list[str]
    choice_texts: list[str]
    required_keywords: list[str] = field(default_factory=list)
    required_world_flags: list[str] = field(default_factory=list)
    required_memory_types: list[str] = field(default_factory=list)
    required_canon_types: list[str] = field(default_factory=list)
    impact_level: int = 3
    world_flags_add: list[str] = field(default_factory=list)
    relationship_deltas: dict[str, int] = field(default_factory=dict)
    loyalty_deltas: dict[str, int] = field(default_factory=dict)
    fear_deltas: dict[str, int] = field(default_factory=dict)
    stability_deltas: dict[str, int] = field(default_factory=dict)
    score_effects: dict[str, float] = field(default_factory=dict)
    memory_tags: list[str] = field(default_factory=list)
    system_tags: list[str] = field(default_factory=list)
    action_hints: list[str] = field(default_factory=list)
    allowed_stages: list[str] = field(default_factory=list)
    stage_priority: int = 0
    next_location_id: str | None = None
    consequence: EventConsequence | None = None


@dataclass(slots=True)
class EndingTemplate:
    ending_id: str
    ending_type: str
    summary: str
    min_scores: dict[str, float] = field(default_factory=dict)
    max_scores: dict[str, float] = field(default_factory=dict)
    required_flags: list[str] = field(default_factory=list)
    required_memory_types: list[str] = field(default_factory=list)
    relationship_requirements: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class PackSystemDefinition:
    system_id: str
    name: str
    medium: str
    description: str
    aliases: list[str] = field(default_factory=list)
    allowed_secondary: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PackActionDefinition:
    action_id: str
    label: str
    description: str
    systems: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    required_flags: list[str] = field(default_factory=list)
    blocked_flags: list[str] = field(default_factory=list)
    allowed_stages: list[str] = field(default_factory=list)
    support_only: bool = False
    score_bias: int = 0


@dataclass(slots=True)
class CollisionRuleDefinition:
    primary_system: str
    secondary_system: str
    signature_id: str
    summary: str
    set_flags: list[str] = field(default_factory=list)
    delayed_event_type: str | None = None
    delay_turns: int = 0


@dataclass(slots=True)
class WorldPack:
    pack_id: str
    name: str
    premise: str
    tone: str
    start_location_id: str
    factions: dict[str, str]
    locations: list[LocationSeed]
    npcs: list[NpcSeed]
    event_templates: list[EventTemplate]
    ending_templates: list[EndingTemplate]
    canon_anchors: list[CanonAnchor]
    memory_triggers: list[MemoryTrigger]
    category: str = "narrative"
    tags: list[str] = field(default_factory=list)
    required_modules: list[str] = field(default_factory=list)
    optional_modules: list[str] = field(default_factory=list)
    systems: list[PackSystemDefinition] = field(default_factory=list)
    action_registry: list[PackActionDefinition] = field(default_factory=list)
    collision_rules: list[CollisionRuleDefinition] = field(default_factory=list)
    presentation: dict[str, Any] = field(default_factory=dict)
