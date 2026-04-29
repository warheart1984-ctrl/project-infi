from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.contracts.translation import SceneGrammar


@dataclass(slots=True)
class Transition:
    from_scene_id: str
    to_scene_id: str
    transition_type: str
    rationale: str


@dataclass(slots=True)
class StagedUnit:
    scene_id: str
    title: str
    summary: str
    act_id: str
    order_index: int


@dataclass(slots=True)
class StagingLaneInput:
    scene_grammar: SceneGrammar


@dataclass(slots=True)
class StagedPlan:
    progression_plan: str
    staged_units: list[StagedUnit] = field(default_factory=list)
    transitions: list[Transition] = field(default_factory=list)
    escalation_points: list[int] = field(default_factory=list)
    implemented: bool = False
    valid: bool = True
