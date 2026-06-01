from __future__ import annotations

from story_forge.contracts.directional import DirectionalContext, DirectionalLaneInput
from story_forge.contracts.errors import (
    ERROR_INVALID_TARGET,
    ERROR_TARGET_NOT_SUPPORTED,
    raise_pipeline_error,
)
from story_forge.contracts.pipeline import ALLOWED_TARGETS, TARGET_BOTH, TARGET_GAME, TARGET_MOVIE


class DirectionalLaneStub:
    def run(self, lane_input: DirectionalLaneInput) -> DirectionalContext:
        target = lane_input.target.strip().lower()
        if target == TARGET_BOTH:
            raise_pipeline_error(
                error_type=ERROR_TARGET_NOT_SUPPORTED,
                message="target 'both' is not currently supported.",
                failed_stage="directional",
            )
        if target not in ALLOWED_TARGETS:
            raise_pipeline_error(
                error_type=ERROR_INVALID_TARGET,
                message=f"target '{lane_input.target}' is not valid.",
                failed_stage="directional",
            )

        if target == TARGET_MOVIE:
            return DirectionalContext(
                target=target,
                priorities=["continuity", "visual rhythm", "scene readability"],
                constraints=["no gameplay branching", "cinematic target only"],
                valid=True,
            )
        return DirectionalContext(
            target=target,
            priorities=["interaction clarity", "readable progression", "stateful choice surfaces"],
            constraints=["no cinematic shot routing", "game target only"],
            valid=True,
        )
