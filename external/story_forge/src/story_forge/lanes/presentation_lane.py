from __future__ import annotations

from story_forge.contracts.pipeline import (
    FORMAT_INTERACTIVE_SCRIPT,
    FORMAT_SCREENPLAY,
    LUMEN_MODE_CINEMATIC,
    LUMEN_MODE_INTERACTIVE,
    TARGET_GAME,
)
from story_forge.contracts.presentation import PresentationLaneInput, PresentedOutput


def _render_presented_text(lane_input: PresentationLaneInput) -> str:
    target = lane_input.directional_context.target
    units = lane_input.staged_plan.staged_units
    if not units:
        return lane_input.staged_plan.progression_plan

    blocks: list[str] = []
    for unit in units:
        if target == TARGET_GAME:
            blocks.append(f"[{unit.order_index}] {unit.title}\n{unit.summary}")
        else:
            blocks.append(f"SCENE {unit.order_index}: {unit.title}\n{unit.summary}")
    return "\n\n".join(blocks)


class DeterministicPresentationLane:
    """Deterministic presentation output that is safe to hand off downstream."""

    def run(self, lane_input: PresentationLaneInput) -> PresentedOutput:
        target = lane_input.directional_context.target
        if target == TARGET_GAME:
            output_format = FORMAT_INTERACTIVE_SCRIPT
            lumen_mode = LUMEN_MODE_INTERACTIVE
        else:
            output_format = FORMAT_SCREENPLAY
            lumen_mode = LUMEN_MODE_CINEMATIC

        return PresentedOutput(
            text=_render_presented_text(lane_input),
            format=output_format,
            lumen_mode=lumen_mode,
            staged_units=list(lane_input.staged_plan.staged_units),
            implemented=True,
            valid=True,
        )


class PresentationLaneStub:
    """Deterministic presentation shell. LUMEN routing is not allowed here."""

    def run(self, lane_input: PresentationLaneInput) -> PresentedOutput:
        target = lane_input.directional_context.target
        if target == TARGET_GAME:
            output_format = FORMAT_INTERACTIVE_SCRIPT
            lumen_mode = LUMEN_MODE_INTERACTIVE
        else:
            output_format = FORMAT_SCREENPLAY
            lumen_mode = LUMEN_MODE_CINEMATIC

        return PresentedOutput(
            text=_render_presented_text(lane_input),
            format=output_format,
            lumen_mode=lumen_mode,
            staged_units=list(lane_input.staged_plan.staged_units),
            implemented=False,
            valid=True,
        )
