from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.contracts.staging import StagedPlan


@dataclass(slots=True)
class DirectionalLaneInput:
    staged_plan: StagedPlan
    target: str


@dataclass(slots=True)
class DirectionalContext:
    target: str
    priorities: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    valid: bool = True
