from __future__ import annotations

from story_forge.contracts.cinematic import CinematicLaneInput, CinematicPlan, ContinuityHook, Shot
from story_forge.contracts.errors import ERROR_TARGET_MISMATCH, raise_pipeline_error
from story_forge.contracts.staging import Transition
from story_forge.contracts.pipeline import TARGET_MOVIE


class DeterministicCinematicLane:
    """Deterministic movie routing that preserves scene order without inventing canon."""

    def run(self, lane_input: CinematicLaneInput) -> CinematicPlan:
        if lane_input.directional_context.target != TARGET_MOVIE:
            raise_pipeline_error(
                error_type=ERROR_TARGET_MISMATCH,
                message="Cinematic lane only accepts target='movie'.",
                failed_stage="cinematic",
            )

        units = list(lane_input.presented_output.staged_units)
        shots = [
            Shot(
                scene_id=unit.scene_id,
                shot_type="establishing" if index == 0 else "continuation",
                camera_move="slow_push" if index == 0 else "steady_track",
                duration_est=5 if index == 0 else 4,
            )
            for index, unit in enumerate(units)
        ]
        transitions = [
            Transition(
                from_scene_id=current.scene_id,
                to_scene_id=next_unit.scene_id,
                transition_type="cut",
                rationale="preserve deterministic source order across cinematic beats",
            )
            for current, next_unit in zip(units, units[1:])
        ]
        continuity_hooks = [
            ContinuityHook(
                scene_id=current.scene_id,
                hook_type="scene_progression",
                description=f"Carry the established state of '{current.title}' into the next beat.",
                carries_to=next_unit.scene_id,
            )
            for current, next_unit in zip(units, units[1:])
        ]
        return CinematicPlan(
            shots=shots,
            pacing_rules=[
                "preserve extracted scene order",
                "hold continuity between adjacent staged units",
            ],
            transitions=transitions,
            continuity_hooks=continuity_hooks,
            implemented=True,
            valid=True,
        )


class CinematicLaneStub:
    """Movie-only scaffold. No fake shot invention beyond contract placeholders."""

    def run(self, lane_input: CinematicLaneInput) -> CinematicPlan:
        if lane_input.directional_context.target != TARGET_MOVIE:
            raise_pipeline_error(
                error_type=ERROR_TARGET_MISMATCH,
                message="Cinematic lane only accepts target='movie'.",
                failed_stage="cinematic",
            )
        return CinematicPlan(
            shots=[],
            pacing_rules=[],
            transitions=[],
            continuity_hooks=[],
            implemented=False,
            valid=True,
        )
