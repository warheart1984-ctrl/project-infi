from __future__ import annotations

from dataclasses import dataclass

from story_forge.contracts.cinematic import CinematicPlan
from story_forge.contracts.directional import DirectionalContext
from story_forge.contracts.presentation import PresentedOutput
from story_forge.contracts.staging import StagedPlan
from story_forge.contracts.translation import SceneGrammar


@dataclass(slots=True)
class EngineHandoffInput:
    scene_grammar: SceneGrammar
    staged_plan: StagedPlan
    directional_context: DirectionalContext
    presented_output: PresentedOutput
    cinematic_plan: CinematicPlan | None = None
