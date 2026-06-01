from __future__ import annotations

from story_forge.contracts import (
    CinematicPlan,
    CinematicLaneInput,
    DirectionalLaneInput,
    DirectionalContext,
    EngineHandoffInput,
    ERROR_TRANSLATION_NOT_IMPLEMENTED,
    OrchestratorState,
    PipelineContractError,
    PipelineRequest,
    PresentationLaneInput,
    PresentedOutput,
    SceneGrammar,
    STAGE_CINEMATIC,
    STAGE_DIRECTIONAL,
    STAGE_ENGINE_HANDOFF,
    STAGE_PRESENTATION,
    STAGE_STAGING,
    STAGE_TRANSLATION,
    StageResult,
    StagedPlan,
    StagingLaneInput,
    TranslationLaneInput,
    build_contract,
    ensure_contract_instance,
    validate_engine_handoff_contract,
)
from story_forge.contracts.errors import make_error
from story_forge.contracts.pipeline import TARGET_MOVIE
from story_forge.lanes.cinematic_lane import CinematicLaneStub, DeterministicCinematicLane
from story_forge.lanes.directional_lane import DirectionalLaneStub
from story_forge.lanes.presentation_lane import DeterministicPresentationLane, PresentationLaneStub
from story_forge.lanes.staging_lane import DeterministicStagingLane, StagingLaneStub
from story_forge.lanes.translation_lane import DeterministicTranslationLane
from story_forge.orchestrator.interfaces import (
    CinematicLaneProtocol,
    DirectionalLaneProtocol,
    PresentationLaneProtocol,
    StagingLaneProtocol,
    TranslationLaneProtocol,
)


class PipelineOrchestrator:
    def __init__(
        self,
        *,
        translation_lane: TranslationLaneProtocol | None = None,
        staging_lane: StagingLaneProtocol | None = None,
        directional_lane: DirectionalLaneProtocol | None = None,
        presentation_lane: PresentationLaneProtocol | None = None,
        cinematic_lane: CinematicLaneProtocol | None = None,
    ) -> None:
        self.translation_lane = translation_lane or DeterministicTranslationLane()
        self.staging_lane = staging_lane or DeterministicStagingLane()
        self.directional_lane = directional_lane or DirectionalLaneStub()
        self.presentation_lane = presentation_lane or DeterministicPresentationLane()
        self.cinematic_lane = cinematic_lane or DeterministicCinematicLane()

    def run(self, request: PipelineRequest | dict[str, object]) -> OrchestratorState:
        state = OrchestratorState(current_stage=STAGE_TRANSLATION)
        try:
            pipeline_request = self._build_pipeline_request(request)
            self._run_translation_stage(state, pipeline_request)
            self._run_staging_stage(state)
            self._run_directional_stage(state, pipeline_request)
            self._run_presentation_stage(state)
            self._run_cinematic_stage(state)
            self._run_engine_handoff(state)
            state.pipeline_ok = True
            return state
        except PipelineContractError as exc:
            state.pipeline_ok = False
            state.error = exc.error
            state.current_stage = exc.error.failed_stage or state.current_stage
            state.execution_log.append(
                StageResult(
                    stage=state.current_stage,
                    ok=False,
                    detail=exc.error.error_type,
                )
            )
            return state

    def _build_pipeline_request(self, request: PipelineRequest | dict[str, object]) -> PipelineRequest:
        if isinstance(request, PipelineRequest):
            return ensure_contract_instance(request, PipelineRequest, stage=STAGE_TRANSLATION)
        return build_contract(request, PipelineRequest, stage=STAGE_TRANSLATION)

    def _run_translation_stage(self, state: OrchestratorState, request: PipelineRequest) -> None:
        state.current_stage = STAGE_TRANSLATION
        translation_input = TranslationLaneInput(
            raw_text=request.raw_text,
            title=request.title,
            target=request.target,
        )
        scene_grammar = ensure_contract_instance(
            self.translation_lane.run(translation_input),
            SceneGrammar,
            stage=STAGE_TRANSLATION,
        )
        state.last_valid_state.scene_grammar = scene_grammar
        state.last_completed_stage = STAGE_TRANSLATION
        state.execution_log.append(
            StageResult(stage=STAGE_TRANSLATION, ok=True, detail="scene_grammar ready")
        )
        if not scene_grammar.implemented:
            raise PipelineContractError(
                make_error(
                    error_type=ERROR_TRANSLATION_NOT_IMPLEMENTED,
                    message="Translation returned implemented=false. Pipeline must stop.",
                    failed_stage=STAGE_TRANSLATION,
                )
            )

    def _run_staging_stage(self, state: OrchestratorState) -> None:
        state.current_stage = STAGE_STAGING
        staging_input = StagingLaneInput(scene_grammar=state.last_valid_state.scene_grammar)
        staged_plan = ensure_contract_instance(
            self.staging_lane.run(staging_input),
            StagedPlan,
            stage=STAGE_STAGING,
        )
        state.last_valid_state.staged_plan = staged_plan
        state.last_completed_stage = STAGE_STAGING
        state.execution_log.append(
            StageResult(stage=STAGE_STAGING, ok=True, detail="staged_plan ready")
        )

    def _run_directional_stage(self, state: OrchestratorState, request: PipelineRequest) -> None:
        state.current_stage = STAGE_DIRECTIONAL
        directional_input = DirectionalLaneInput(
            staged_plan=state.last_valid_state.staged_plan,
            target=request.target,
        )
        directional_context = ensure_contract_instance(
            self.directional_lane.run(directional_input),
            DirectionalContext,
            stage=STAGE_DIRECTIONAL,
        )
        state.last_valid_state.directional_context = directional_context
        state.last_completed_stage = STAGE_DIRECTIONAL
        state.execution_log.append(
            StageResult(stage=STAGE_DIRECTIONAL, ok=True, detail=f"target={directional_context.target}")
        )

    def _run_presentation_stage(self, state: OrchestratorState) -> None:
        state.current_stage = STAGE_PRESENTATION
        presentation_input = PresentationLaneInput(
            staged_plan=state.last_valid_state.staged_plan,
            directional_context=state.last_valid_state.directional_context,
        )
        presented_output = ensure_contract_instance(
            self.presentation_lane.run(presentation_input),
            PresentedOutput,
            stage=STAGE_PRESENTATION,
        )
        state.last_valid_state.presented_output = presented_output
        state.last_completed_stage = STAGE_PRESENTATION
        state.execution_log.append(
            StageResult(stage=STAGE_PRESENTATION, ok=True, detail=f"format={presented_output.format}")
        )

    def _run_cinematic_stage(self, state: OrchestratorState) -> None:
        directional_context = state.last_valid_state.directional_context
        if directional_context is None or directional_context.target != TARGET_MOVIE:
            state.last_valid_state.cinematic_plan = None
            return

        state.current_stage = STAGE_CINEMATIC
        cinematic_input = CinematicLaneInput(
            presented_output=state.last_valid_state.presented_output,
            directional_context=directional_context,
        )
        cinematic_plan = ensure_contract_instance(
            self.cinematic_lane.run(cinematic_input),
            CinematicPlan,
            stage=STAGE_CINEMATIC,
        )
        state.last_valid_state.cinematic_plan = cinematic_plan
        state.last_completed_stage = STAGE_CINEMATIC
        state.execution_log.append(
            StageResult(stage=STAGE_CINEMATIC, ok=True, detail="cinematic_plan ready")
        )

    def _run_engine_handoff(self, state: OrchestratorState) -> None:
        state.current_stage = STAGE_ENGINE_HANDOFF
        handoff = EngineHandoffInput(
            scene_grammar=state.last_valid_state.scene_grammar,
            staged_plan=state.last_valid_state.staged_plan,
            directional_context=state.last_valid_state.directional_context,
            presented_output=state.last_valid_state.presented_output,
            cinematic_plan=state.last_valid_state.cinematic_plan,
        )
        state.engine_handoff = validate_engine_handoff_contract(handoff)
        state.last_completed_stage = STAGE_ENGINE_HANDOFF
        state.execution_log.append(
            StageResult(stage=STAGE_ENGINE_HANDOFF, ok=True, detail="engine handoff ready")
        )
