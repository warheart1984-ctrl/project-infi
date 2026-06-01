from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.models import (
    ARIS_MEMORY_LAYERS,
    CanonMode,
    DirectiveType,
    EventConsequence,
    PRESENTATION_MODES,
    RUNTIME_MODES,
    StoryState,
)
from story_forge.scenario_rules import SCENARIO_STAGE_RULES


class StoryValidationError(ValueError):
    pass


@dataclass(slots=True)
class RuntimeIntegrityReport:
    """Structured report separating hard failures from soft observations."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_state(state: StoryState) -> list[str]:
    issues: list[str] = []

    canonical_deaths = {
        entry.subject_id
        for entry in state.canon_ledger
        if not entry.retracted and entry.entry_type == "death"
    }
    for character_id in canonical_deaths:
        character = state.characters.get(character_id)
        if character and character.alive:
            issues.append(
                f"Character '{character_id}' is alive in character state but marked dead in canon."
            )

    seen: dict[tuple[str, str], str] = {}
    for entry in state.canon_ledger:
        if entry.retracted:
            continue
        key = (entry.entry_type, entry.subject_id)
        if key in seen and seen[key] != entry.description:
            if state.canon_mode == CanonMode.FIXED:
                issues.append(
                    f"Conflicting canon entries for {entry.entry_type}:{entry.subject_id} in fixed mode."
                )
        else:
            seen[key] = entry.description

    for directive in state.directives:
        if directive.kind == DirectiveType.ONE_TIME and directive.consumed and directive.enabled:
            issues.append(
                f"One-time directive '{directive.directive_id}' is still enabled after consumption."
            )

    runtime_memory = state.aris_runtime.governed_memory
    for layer in ARIS_MEMORY_LAYERS:
        if layer not in runtime_memory:
            issues.append(f"ARIS runtime memory layer '{layer}' is missing.")

    kill_mode = str(state.aris_runtime.kill_switch.get("mode", "nominal"))
    if kill_mode not in {"nominal", "degraded", "lockdown"}:
        issues.append(f"ARIS runtime kill switch mode '{kill_mode}' is invalid.")

    for entry in state.llm_history:
        mode = str(entry.get("mode", ""))
        if mode and mode not in PRESENTATION_MODES:
            issues.append(f"LLM history mode '{mode}' is invalid.")

    if state.runtime_mode not in RUNTIME_MODES:
        issues.append(f"Story runtime mode '{state.runtime_mode}' is invalid.")

    installed_board_ids = set(state.installed_boards)
    if state.board_runtime.active_board_id and state.board_runtime.active_board_id not in installed_board_ids:
        issues.append(
            f"Active board '{state.board_runtime.active_board_id}' is not installed."
        )
    if state.board_runtime.mounted_board_id and state.board_runtime.mounted_board_id not in installed_board_ids:
        issues.append(
            f"Mounted board '{state.board_runtime.mounted_board_id}' is not installed."
        )
    if state.system_state.secondary_system and state.system_state.secondary_system == state.system_state.active_system:
        issues.append("Secondary system cannot equal active system.")
    if state.system_state.collision_mode and not state.system_state.secondary_system:
        issues.append("Collision mode cannot be enabled without a secondary system.")

    pending_scheduled: set[tuple[str, int, str | None]] = set()
    for event in state.scheduled_events:
        key = (event.event_type, event.trigger_turn, event.source_event_id)
        if not event.fired:
            if key in pending_scheduled:
                issues.append(
                    f"Duplicate unfired scheduled event for {event.event_type} at turn {event.trigger_turn}."
                )
            pending_scheduled.add(key)
        if event.trigger_turn < 0:
            issues.append(f"Scheduled event '{event.scheduled_id}' has a negative trigger turn.")

    visual_artifact_ids = state.visual_memory.artifact_ids
    if len(visual_artifact_ids) != len(set(visual_artifact_ids)):
        issues.append("Visual memory contains duplicate artifact ids.")

    return issues


def ensure_valid_state(state: StoryState) -> None:
    issues = validate_state(state)
    if issues:
        raise StoryValidationError(" | ".join(issues))


def validate_story_forge_runtime_coherence(state: StoryState) -> RuntimeIntegrityReport:
    """Return coherence violations for Story Forge runtime state."""
    report = RuntimeIntegrityReport()

    if state.runtime_mode not in RUNTIME_MODES:
        report.errors.append(f"invalid runtime_mode: {state.runtime_mode}")
    elif state.runtime_mode != "story_forge":
        report.errors.append(f"invalid runtime_mode: {state.runtime_mode}")

    scenario = state.scenario_position
    if not scenario.current_arc:
        report.errors.append("scenario current_arc is empty")
    if not scenario.current_stage:
        report.errors.append("scenario current_stage is empty")
    if scenario.entered_stage_turn < 0:
        report.errors.append("scenario entered_stage_turn is negative")
    if scenario.stage_turn_count < 0:
        report.errors.append("scenario stage_turn_count is negative")

    if scenario.current_arc:
        valid_stages = _valid_stages_for_arc(scenario.current_arc)
        if valid_stages and scenario.current_stage not in valid_stages:
            report.errors.append(
                f"scenario stage '{scenario.current_stage}' is not valid for arc '{scenario.current_arc}'"
            )
        if not valid_stages:
            report.warnings.append(
                f"no scenario rules loaded for arc '{scenario.current_arc}'"
            )

    for scheduled_event in state.scheduled_events:
        scheduled_id = getattr(scheduled_event, "scheduled_id", "")
        event_type = getattr(scheduled_event, "event_type", "")
        trigger_turn = getattr(scheduled_event, "trigger_turn", -1)
        fired = bool(getattr(scheduled_event, "fired", False))

        if not scheduled_id:
            report.errors.append("scheduled event missing scheduled_id")
        if not event_type:
            report.errors.append("scheduled event missing event_type")
        if trigger_turn < 0:
            report.errors.append(
                f"scheduled event '{scheduled_id or '<missing>'}' has negative trigger_turn"
            )
        if not fired and trigger_turn < state.turn_count:
            report.warnings.append(
                f"scheduled event '{scheduled_id or '<missing>'}' is overdue but unfired"
            )

    unresolved_active_ids: set[str] = set()
    for active_event in state.active_events:
        event_id = getattr(active_event, "event_id", "")
        event_type = getattr(active_event, "event_type", "")
        started_turn = getattr(active_event, "started_turn", -1)
        expires_turn = getattr(active_event, "expires_turn", None)
        resolved = bool(getattr(active_event, "resolved", False))

        if not event_id:
            report.errors.append("active event missing event_id")
        if not event_type:
            report.errors.append("active event missing event_type")
        if started_turn < 0:
            report.errors.append(
                f"active event '{event_id or '<missing>'}' has negative started_turn"
            )
        if expires_turn is not None and expires_turn < started_turn:
            report.errors.append(
                f"active event '{event_id or '<missing>'}' expires before it starts"
            )
        if not resolved and event_id:
            if event_id in unresolved_active_ids:
                report.errors.append(f"duplicate unresolved active event id: {event_id}")
            unresolved_active_ids.add(event_id)

    current_location_id = state.player_state.current_location_id
    if not current_location_id:
        report.errors.append("player current_location_id is empty")
    elif state.world_state.locations and current_location_id not in state.world_state.locations:
        report.errors.append(
            f"player current_location_id '{current_location_id}' not found in world state"
        )

    installed_board_ids = set(state.installed_boards)
    if state.board_runtime.active_board_id and state.board_runtime.active_board_id not in installed_board_ids:
        report.errors.append(
            f"active board '{state.board_runtime.active_board_id}' is not installed"
        )
    if state.board_runtime.mounted_board_id and state.board_runtime.mounted_board_id not in installed_board_ids:
        report.errors.append(
            f"mounted board '{state.board_runtime.mounted_board_id}' is not installed"
        )
    if state.system_state.secondary_system and state.system_state.secondary_system == state.system_state.active_system:
        report.errors.append("system secondary_system must differ from active_system")
    if state.system_state.collision_mode and not state.system_state.secondary_system:
        report.errors.append("collision mode requires a secondary system")

    for transition in state.location_history:
        if not getattr(transition, "from_location", ""):
            report.errors.append("location transition missing from_location")
        if not getattr(transition, "to_location", ""):
            report.errors.append("location transition missing to_location")
        if getattr(transition, "turn_number", -1) < 0:
            report.errors.append("location transition has negative turn_number")
        if not getattr(transition, "cause", ""):
            report.errors.append("location transition missing cause")

    for event in state.recent_events:
        _validate_event_consequence(report, state, event)

    return report


def _valid_stages_for_arc(arc: str) -> set[str]:
    rules = [rule for rule in SCENARIO_STAGE_RULES if rule.arc == arc]
    stages = {rule.stage for rule in rules if rule.stage}
    stages.update(rule.next_stage for rule in rules if rule.next_stage)
    return {stage for stage in stages if stage}


def _validate_event_consequence(
    report: RuntimeIntegrityReport,
    state: StoryState,
    event: object,
) -> None:
    consequence = getattr(event, "consequence", None)
    if consequence is None:
        consequence = getattr(event, "consequences", None)
    if consequence is None:
        return

    if isinstance(consequence, EventConsequence):
        schedule_event_type = consequence.schedule_event_type
        schedule_delay_turns = consequence.schedule_delay_turns
        move_to_location_id = consequence.move_to_location_id
        advance_to_stage = consequence.advance_to_stage
    else:
        schedule_event_type = getattr(consequence, "schedule_event_type", None)
        schedule_delay_turns = getattr(consequence, "schedule_delay_turns", None)
        move_to_location_id = getattr(consequence, "move_to_location_id", None)
        advance_to_stage = getattr(consequence, "advance_to_stage", None)

    if schedule_event_type and schedule_delay_turns is None:
        report.errors.append("event consequence schedules event type without delay")
    if schedule_delay_turns is not None and not schedule_event_type:
        report.errors.append("event consequence has schedule_delay_turns without schedule_event_type")
    if schedule_delay_turns is not None and schedule_delay_turns < 0:
        report.errors.append("event consequence has negative schedule_delay_turns")
    if move_to_location_id and state.world_state.locations and move_to_location_id not in state.world_state.locations:
        report.errors.append(
            f"event consequence move_to_location_id '{move_to_location_id}' not found in world state"
        )
    if advance_to_stage:
        valid_stages = _valid_stages_for_arc(state.scenario_position.current_arc)
        if valid_stages and advance_to_stage not in valid_stages:
            report.errors.append(
                f"event consequence advance_to_stage '{advance_to_stage}' is not valid for arc "
                f"'{state.scenario_position.current_arc}'"
            )
