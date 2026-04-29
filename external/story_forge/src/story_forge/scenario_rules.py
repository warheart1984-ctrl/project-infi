from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.models import StoryState


@dataclass(slots=True)
class ScenarioStageRule:
    arc: str
    stage: str
    next_stage: str | None = None
    min_turns_in_stage: int = 0
    required_flags: dict[str, bool] = field(default_factory=dict)
    required_event_types: list[str] = field(default_factory=list)
    allow_flag_catchup: bool = False


SCENARIO_STAGE_RULES: tuple[ScenarioStageRule, ...] = (
    ScenarioStageRule(
        arc="charming_knife",
        stage="opening",
        next_stage="crossings",
        min_turns_in_stage=1,
        required_flags={"crossing_started": True},
        required_event_types=["threshold"],
        allow_flag_catchup=True,
    ),
    ScenarioStageRule(
        arc="charming_knife",
        stage="crossings",
        next_stage="underworld",
        min_turns_in_stage=1,
        required_flags={"ghostline_entered": True},
        required_event_types=["travel"],
        allow_flag_catchup=True,
    ),
    ScenarioStageRule(
        arc="charming_knife",
        stage="underworld",
        next_stage="ashes",
        min_turns_in_stage=1,
        required_flags={"ashenreach_entered": True},
        required_event_types=["travel"],
        allow_flag_catchup=True,
    ),
    ScenarioStageRule(
        arc="charming_knife",
        stage="ashes",
        next_stage="court",
        min_turns_in_stage=1,
        required_flags={"valedour_entered": True},
        required_event_types=["travel"],
        allow_flag_catchup=True,
    ),
    ScenarioStageRule(
        arc="charming_knife",
        stage="court",
        next_stage="convergence",
        min_turns_in_stage=1,
        required_flags={"mirror_court_breached": True},
        required_event_types=["collision"],
        allow_flag_catchup=True,
    ),
    ScenarioStageRule(
        arc="charming_knife",
        stage="convergence",
        next_stage="aftermath",
        min_turns_in_stage=1,
        required_flags={"pattern_broken": True},
        required_event_types=["resolution_choice"],
        allow_flag_catchup=True,
    ),
    ScenarioStageRule(
        arc="ashen_fall",
        stage="opening",
        next_stage="crossing",
        min_turns_in_stage=1,
        required_event_types=["travel"],
    ),
    ScenarioStageRule(
        arc="ashen_fall",
        stage="crossing",
        next_stage="reckoning",
        min_turns_in_stage=1,
        required_flags={"bell_rung": True},
        required_event_types=["resolution"],
    ),
    ScenarioStageRule(
        arc="ashen_fall",
        stage="reckoning",
        next_stage="endgame",
        min_turns_in_stage=1,
        required_flags={"gate_confronted": True},
        required_event_types=["resolution"],
    ),
    ScenarioStageRule(
        arc="brindle_hollow",
        stage="opening",
        next_stage="recognition",
        min_turns_in_stage=1,
        required_event_types=["social_revelation"],
    ),
    ScenarioStageRule(
        arc="brindle_hollow",
        stage="recognition",
        next_stage="approach",
        min_turns_in_stage=1,
        required_flags={"approach_started": True},
        required_event_types=["threshold"],
    ),
    ScenarioStageRule(
        arc="brindle_hollow",
        stage="approach",
        next_stage="reckoning",
        min_turns_in_stage=1,
        required_flags={"origin_seen": True},
        required_event_types=["ritual_memory"],
    ),
    ScenarioStageRule(
        arc="brindle_hollow",
        stage="reckoning",
        next_stage="aftermath",
        min_turns_in_stage=1,
        required_flags={"final_choice_reached": True},
        required_event_types=["resolution_choice"],
    ),
    ScenarioStageRule(
        arc="velvet_system",
        stage="opening",
        next_stage="threads",
        min_turns_in_stage=1,
        required_event_types=["discovery"],
    ),
    ScenarioStageRule(
        arc="velvet_system",
        stage="threads",
        next_stage="collision",
        min_turns_in_stage=1,
        required_flags={"oath_threaded": True, "syntax_touched": True},
        required_event_types=["collision"],
    ),
    ScenarioStageRule(
        arc="velvet_system",
        stage="collision",
        next_stage="revision",
        min_turns_in_stage=1,
        required_flags={"identity_drift_visible": True},
        required_event_types=["collision"],
    ),
    ScenarioStageRule(
        arc="velvet_system",
        stage="revision",
        next_stage="aftermath",
        min_turns_in_stage=1,
        required_flags={"final_revision_chosen": True},
        required_event_types=["resolution"],
    ),
)


def evaluate_scenario_progression(
    state: StoryState,
) -> str | None:
    """Return next stage if progression conditions are met, else None."""
    path = collect_scenario_progression_path(state, max_steps=1)
    return path[0] if path else None


def collect_scenario_progression_path(
    state: StoryState,
    *,
    max_steps: int | None = None,
) -> list[str]:
    """Return a sequential list of stage advances supported by current state."""
    current_arc = state.scenario_position.current_arc
    current_stage = state.scenario_position.current_stage
    stage_turns = state.scenario_position.stage_turn_count
    arc_flags = state.scenario_position.arc_flags
    observed_event_types = {
        event.event_type
        for event in state.recent_events
    } | {
        event.event_type
        for event in state.active_events
    }
    rules_for_arc = [rule for rule in SCENARIO_STAGE_RULES if rule.arc == current_arc]
    limit = max_steps if max_steps is not None else max(1, len(rules_for_arc))
    path: list[str] = []
    visited_stages = {current_stage}

    for _ in range(limit):
        rule = next(
            (
                candidate
                for candidate in rules_for_arc
                if candidate.stage == current_stage
            ),
            None,
        )
        if rule is None or rule.next_stage is None:
            break
        if _rule_requirements_match(rule, stage_turns, arc_flags, observed_event_types) or _force_stage_progression(rule, arc_flags):
            next_stage = rule.next_stage
            if next_stage in visited_stages:
                break
            path.append(next_stage)
            visited_stages.add(next_stage)
            current_stage = next_stage
            stage_turns = 0
            continue
        break

    return path


def _rule_requirements_match(
    rule: ScenarioStageRule,
    stage_turns: int,
    arc_flags: dict[str, bool],
    observed_event_types: set[str],
) -> bool:
    if stage_turns < rule.min_turns_in_stage:
        return False
    if any(arc_flags.get(flag_name) != flag_value for flag_name, flag_value in rule.required_flags.items()):
        return False
    if any(event_type not in observed_event_types for event_type in rule.required_event_types):
        return False
    return True


def _force_stage_progression(
    rule: ScenarioStageRule,
    arc_flags: dict[str, bool],
) -> bool:
    """Allow accumulated rule flags to catch a stale stage up to runtime truth."""
    if not rule.allow_flag_catchup or not rule.required_flags:
        return False
    return all(arc_flags.get(flag_name) == flag_value for flag_name, flag_value in rule.required_flags.items())
