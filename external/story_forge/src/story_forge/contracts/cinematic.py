from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.contracts.directional import DirectionalContext
from story_forge.contracts.presentation import PresentedOutput
from story_forge.contracts.staging import Transition


@dataclass(slots=True)
class ContinuityHook:
    scene_id: str
    hook_type: str
    description: str
    carries_to: str


@dataclass(slots=True)
class Shot:
    scene_id: str
    shot_type: str
    camera_move: str
    duration_est: int


@dataclass(slots=True)
class CinematicLaneInput:
    presented_output: PresentedOutput
    directional_context: DirectionalContext


@dataclass(slots=True)
class CinematicPlan:
    shots: list[Shot] = field(default_factory=list)
    pacing_rules: list[str] = field(default_factory=list)
    transitions: list[Transition] = field(default_factory=list)
    continuity_hooks: list[ContinuityHook] = field(default_factory=list)
    implemented: bool = False
    valid: bool = True
