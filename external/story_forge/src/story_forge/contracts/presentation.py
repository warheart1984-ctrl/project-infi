from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.contracts.directional import DirectionalContext
from story_forge.contracts.staging import StagedPlan, StagedUnit


@dataclass(slots=True)
class PresentationLaneInput:
    staged_plan: StagedPlan
    directional_context: DirectionalContext


@dataclass(slots=True)
class PresentedOutput:
    text: str
    format: str
    lumen_mode: str
    staged_units: list[StagedUnit] = field(default_factory=list)
    implemented: bool = False
    valid: bool = True
