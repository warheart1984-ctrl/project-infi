from __future__ import annotations

from story_forge.contracts.staging import StagedPlan, StagedUnit, StagingLaneInput, Transition


def _build_source_order_plan(
    lane_input: StagingLaneInput,
    *,
    progression_plan: str,
    implemented: bool,
) -> StagedPlan:
    staged_units: list[StagedUnit] = []
    for act_index, act in enumerate(lane_input.scene_grammar.acts, start=1):
        for scene in act.scenes:
            staged_units.append(
                StagedUnit(
                    scene_id=scene.scene_id,
                    title=scene.title,
                    summary=scene.summary,
                    act_id=act.act_id or f"act_{act_index:02d}",
                    order_index=len(staged_units) + 1,
                )
            )
    transitions = [
        Transition(
            from_scene_id=current.scene_id,
            to_scene_id=next_unit.scene_id,
            transition_type="source_order",
            rationale="preserve extracted order",
        )
        for current, next_unit in zip(staged_units, staged_units[1:])
    ]
    escalation_points = [len(staged_units)] if staged_units else []
    return StagedPlan(
        progression_plan=progression_plan,
        staged_units=staged_units,
        transitions=transitions,
        escalation_points=escalation_points,
        implemented=implemented,
        valid=True,
    )


class DeterministicStagingLane:
    """Lawful source-order staging used by the default pipeline path."""

    def run(self, lane_input: StagingLaneInput) -> StagedPlan:
        return _build_source_order_plan(
            lane_input,
            progression_plan=(
                "Deterministic staging preserves extracted scene order for backend handoff."
            ),
            implemented=True,
        )


class StagingLaneStub:
    """Deterministic source-order staging shell with no target or cinematic logic."""

    def run(self, lane_input: StagingLaneInput) -> StagedPlan:
        return _build_source_order_plan(
            lane_input,
            progression_plan=(
                "Scaffold staging preserves extracted scene order without adding new structure."
            ),
            implemented=False,
        )
