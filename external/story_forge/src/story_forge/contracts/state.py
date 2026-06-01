from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.contracts.cinematic import CinematicPlan
from story_forge.contracts.directional import DirectionalContext
from story_forge.contracts.engine_handoff import EngineHandoffInput
from story_forge.contracts.errors import PipelineError
from story_forge.contracts.presentation import PresentedOutput
from story_forge.contracts.staging import StagedPlan
from story_forge.contracts.translation import SceneGrammar


@dataclass(slots=True)
class LastValidState:
    scene_grammar: SceneGrammar | None = None
    staged_plan: StagedPlan | None = None
    directional_context: DirectionalContext | None = None
    presented_output: PresentedOutput | None = None
    cinematic_plan: CinematicPlan | None = None


@dataclass(slots=True)
class StageResult:
    stage: str
    ok: bool
    detail: str


@dataclass(slots=True)
class OrchestratorState:
    current_stage: str = "translation"
    last_completed_stage: str | None = None
    last_valid_state: LastValidState = field(default_factory=LastValidState)
    pipeline_ok: bool = False
    error: PipelineError | None = None
    execution_log: list[StageResult] = field(default_factory=list)
    engine_handoff: EngineHandoffInput | None = None
    support_resume_from_last_valid_stage: bool = False
