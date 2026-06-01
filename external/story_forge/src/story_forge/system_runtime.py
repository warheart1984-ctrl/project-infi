from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.models import StoryRequest, StoryState, utc_now
from story_forge.state_manager import schedule_event
from story_forge.worldpacks.base import (
    CollisionRuleDefinition,
    EventTemplate,
    PackActionDefinition,
    PackSystemDefinition,
    WorldPack,
)


@dataclass(slots=True)
class ActionSelectionResult:
    primary_action_id: str | None = None
    support_action_ids: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)


def resolve_system_state(
    world_pack: WorldPack,
    state: StoryState,
    request: StoryRequest,
    selected_template: EventTemplate | None,
) -> list[str]:
    systems = {system.system_id: system for system in world_pack.systems}
    if not systems:
        state.system_state.active_system = "narrative"
        state.system_state.secondary_system = None
        state.system_state.collision_mode = False
        state.system_state.decision_trace = ["no explicit authored systems"]
        return list(state.system_state.decision_trace)

    candidate_ids = _candidate_system_ids(world_pack, request.player_input, selected_template)
    active_system = candidate_ids[0] if candidate_ids else next(iter(systems))
    secondary_system = None
    collision_mode = False
    trace = [f"active system resolved: {active_system}"]

    for candidate in candidate_ids[1:]:
        if candidate == active_system:
            continue
        collision_rule = _collision_rule(world_pack, active_system, candidate)
        if _secondary_allowed(systems[active_system], systems[candidate]) or collision_rule is not None:
            secondary_system = candidate
            collision_mode = collision_rule is not None
            trace.append(
                f"secondary system admitted: {candidate}"
                + (" via collision rule" if collision_rule is not None else "")
            )
            break
        if state.system_state.medium_discipline:
            trace.append(f"medium discipline suppressed unlawful secondary system: {candidate}")

    state.system_state.active_system = active_system
    state.system_state.secondary_system = secondary_system
    state.system_state.collision_mode = collision_mode
    state.system_state.decision_trace = trace[-12:]
    state.updated_at = utc_now()
    return list(state.system_state.decision_trace)


def apply_collision_rules(
    world_pack: WorldPack,
    state: StoryState,
    current_turn: int,
) -> list[str]:
    active_system = state.system_state.active_system
    secondary_system = state.system_state.secondary_system
    if not state.system_state.collision_mode or not active_system or not secondary_system:
        return []

    rule = _collision_rule(world_pack, active_system, secondary_system)
    if rule is None:
        state.system_state.collision_mode = False
        state.updated_at = utc_now()
        return ["collision mode cleared: no matching authored collision rule"]

    trace = [f"collision signature applied: {rule.signature_id}"]
    collision_flag = f"collision_signature_{rule.signature_id}"
    if collision_flag not in state.world_state.environment_flags:
        state.world_state.environment_flags.append(collision_flag)
    for flag in rule.set_flags:
        if flag not in state.world_state.environment_flags:
            state.world_state.environment_flags.append(flag)
    if rule.delayed_event_type:
        schedule_event(
            state=state,
            event_type=rule.delayed_event_type,
            trigger_turn=current_turn + max(0, rule.delay_turns),
            source="collision",
            payload={"collision_signature": rule.signature_id},
        )
        trace.append(
            f"scheduled delayed consequence: {rule.delayed_event_type} at turn {current_turn + max(0, rule.delay_turns)}"
        )
    state.system_state.last_collision_signature = rule.signature_id
    state.updated_at = utc_now()
    return trace


def select_admitted_actions(
    world_pack: WorldPack,
    state: StoryState,
    request: StoryRequest,
    selected_template: EventTemplate | None,
) -> ActionSelectionResult:
    if not world_pack.action_registry:
        state.system_state.primary_action_id = None
        state.system_state.support_action_ids = []
        return ActionSelectionResult(trace=["no authored action registry"])

    lowered = request.player_input.lower()
    current_stage = state.scenario_position.current_stage
    flags = set(state.world_state.environment_flags)
    active_systems = {
        system_id
        for system_id in (state.system_state.active_system, state.system_state.secondary_system)
        if system_id
    }
    ranked: list[tuple[int, str, PackActionDefinition]] = []

    for action in world_pack.action_registry:
        if action.allowed_stages and current_stage not in action.allowed_stages:
            continue
        if action.required_flags and not set(action.required_flags).issubset(flags):
            continue
        if set(action.blocked_flags) & flags:
            continue
        if action.systems and not active_systems.intersection(action.systems):
            continue

        score = action.score_bias
        if any(keyword in lowered for keyword in action.keywords):
            score += 4
        if selected_template and action.action_id in selected_template.action_hints:
            score += 8
        if state.system_state.active_system and state.system_state.active_system in action.systems:
            score += 2
        if state.system_state.secondary_system and state.system_state.secondary_system in action.systems:
            score += 1
        if score > 0:
            ranked.append((score, action.action_id, action))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    result = ActionSelectionResult()
    action_budget = 2

    for _, _, action in ranked:
        if result.primary_action_id is None and not action.support_only:
            result.primary_action_id = action.action_id
            result.trace.append(f"primary action admitted: {action.action_id}")
            continue
        if len(result.support_action_ids) >= max(0, action_budget - 1):
            break
        result.support_action_ids.append(action.action_id)
        result.trace.append(f"support action admitted: {action.action_id}")

    if result.primary_action_id is None:
        result.trace.append("no primary action admitted")

    state.system_state.primary_action_id = result.primary_action_id
    state.system_state.support_action_ids = list(result.support_action_ids)
    state.system_state.decision_trace = (state.system_state.decision_trace + result.trace)[-12:]
    state.updated_at = utc_now()
    return result


def _candidate_system_ids(
    world_pack: WorldPack,
    player_input: str,
    selected_template: EventTemplate | None,
) -> list[str]:
    seen: list[str] = []
    if selected_template is not None:
        for system_id in selected_template.system_tags:
            if system_id and system_id not in seen:
                seen.append(system_id)
    lowered = player_input.lower()
    for system in world_pack.systems:
        if any(alias in lowered for alias in system.aliases):
            if system.system_id not in seen:
                seen.append(system.system_id)
    return seen


def _secondary_allowed(primary: PackSystemDefinition, secondary: PackSystemDefinition) -> bool:
    return (
        secondary.system_id in primary.allowed_secondary
        or primary.system_id in secondary.allowed_secondary
        or primary.medium == secondary.medium
    )


def _collision_rule(
    world_pack: WorldPack,
    primary_system: str,
    secondary_system: str,
) -> CollisionRuleDefinition | None:
    for rule in world_pack.collision_rules:
        if (
            rule.primary_system == primary_system
            and rule.secondary_system == secondary_system
        ) or (
            rule.primary_system == secondary_system
            and rule.secondary_system == primary_system
        ):
            return rule
    return None
