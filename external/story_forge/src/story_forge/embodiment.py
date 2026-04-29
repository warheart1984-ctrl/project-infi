from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from story_forge.models import Event, OutputPackage, Scene, StoryRequest, StoryState
from story_forge.turn_routing import RouterEmotionSignal, TurnCategoryDecision


@dataclass(slots=True)
class AllowedScope:
    source: str
    runtime_mode: str
    world_pack_id: str | None
    category: str
    mutation_flag: str
    current_location_id: str
    mode: str = "interactive"
    time_progression_allowed: bool = False
    world_fact_mutation_allowed: bool = False
    inventory_mutation_allowed: bool = False
    relationship_mutation_allowed: bool = False
    allowed_location_ids: list[str] = field(default_factory=list)
    allowed_character_ids: list[str] = field(default_factory=list)
    allowed_relationship_ids: list[str] = field(default_factory=list)
    allowed_surface_channels: list[str] = field(default_factory=list)
    pending_constraints: list[str] = field(default_factory=list)
    forced_transition_visible: bool = False
    command_boundary: str = "story_turn"

    def to_payload(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "runtime_mode": self.runtime_mode,
            "world_pack_id": self.world_pack_id,
            "category": self.category,
            "mutation_flag": self.mutation_flag,
            "current_location_id": self.current_location_id,
            "mode": self.mode,
            "time_progression_allowed": self.time_progression_allowed,
            "world_fact_mutation_allowed": self.world_fact_mutation_allowed,
            "inventory_mutation_allowed": self.inventory_mutation_allowed,
            "relationship_mutation_allowed": self.relationship_mutation_allowed,
            "allowed_location_ids": list(self.allowed_location_ids),
            "allowed_character_ids": list(self.allowed_character_ids),
            "allowed_relationship_ids": list(self.allowed_relationship_ids),
            "allowed_surface_channels": list(self.allowed_surface_channels),
            "pending_constraints": list(self.pending_constraints),
            "forced_transition_visible": self.forced_transition_visible,
            "command_boundary": self.command_boundary,
        }


@dataclass(slots=True)
class ShapedTurnContract:
    category: str
    mutation_flag: str
    dialogue_effect: str | None
    mode: str
    allowed: bool
    forced_transition: bool
    anti_loop_correction: bool
    anti_loop_rules_fired: list[str]
    required_state_delta: bool
    discharge_target: str | None
    blocked_reason: str | None
    constraints: list[str]
    router_emotion: RouterEmotionSignal | None
    allowed_scope: AllowedScope
    source: str = "router_derived"

    def to_payload(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "mutation_flag": self.mutation_flag,
            "dialogue_effect": self.dialogue_effect,
            "mode": self.mode,
            "allowed": self.allowed,
            "forced_transition": self.forced_transition,
            "anti_loop_correction": self.anti_loop_correction,
            "anti_loop_rules_fired": list(self.anti_loop_rules_fired),
            "required_state_delta": self.required_state_delta,
            "discharge_target": self.discharge_target,
            "blocked_reason": self.blocked_reason,
            "constraints": list(self.constraints),
            "router_emotion": (
                self.router_emotion.to_payload() if self.router_emotion is not None else None
            ),
            "allowed_scope": self.allowed_scope.to_payload(),
            "source": self.source,
        }


@dataclass(slots=True)
class EmbodimentValidationResult:
    valid: bool
    blocked_commit: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "blocked_commit": self.blocked_commit,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def build_shaped_turn_contract(
    state: StoryState,
    request: StoryRequest,
    turn_category: TurnCategoryDecision | None,
    scene: Scene,
    events: list[Event],
    *,
    requested_lane: str | None = None,
) -> ShapedTurnContract:
    category = (
        turn_category.resolved_category
        if turn_category is not None
        else "scene_advancement"
    )
    mutation_flag = (
        turn_category.mutation_flag
        if turn_category is not None
        else "mutating"
    )
    command_boundary = "story_turn"
    if requested_lane is not None:
        command_boundary = f"{requested_lane}:non_story"
    allowed_character_ids = _ordered_unique(
        [
            "player",
            *scene.characters,
            *(participant for event in events for participant in event.participants),
        ]
    )
    current_location_id = state.player_state.current_location_id or "unknown"
    allowed_location_ids = _ordered_unique(
        [
            current_location_id,
            *(event.location_id for event in events if event.location_id),
            *(event.next_location_id for event in events if event.next_location_id),
        ]
    )
    allowed_relationship_ids = [
        character_id for character_id in allowed_character_ids if character_id != "player"
    ]
    pending_constraints = [
        "approved_hooks_only",
        "no_free_text_inference",
        "presentation_non_authoritative",
    ]
    if turn_category is not None and turn_category.injected_conflict:
        pending_constraints.append("anti_loop_conflict_injected")
    if turn_category is not None and turn_category.forced_transition:
        pending_constraints.append("forced_transition_naturalized")
    if requested_lane is not None:
        pending_constraints.append("slash_command_non_story")
    allowed_scope = AllowedScope(
        source="router_state_snapshot+scene_shape",
        runtime_mode=state.runtime_mode,
        world_pack_id=state.world_pack_id,
        category=category,
        mutation_flag=mutation_flag,
        current_location_id=current_location_id,
        mode="interactive",
        time_progression_allowed=mutation_flag == "mutating",
        world_fact_mutation_allowed=mutation_flag == "mutating" and requested_lane is None,
        inventory_mutation_allowed=category == "state_update",
        relationship_mutation_allowed=bool(
            turn_category is not None
            and turn_category.dialogue_effect in {"relational", "informational"}
        ),
        allowed_location_ids=allowed_location_ids,
        allowed_character_ids=allowed_character_ids,
        allowed_relationship_ids=allowed_relationship_ids,
        allowed_surface_channels=[
            "scene.text",
            "presentation.text",
            "presentation_hooks",
            "visual_recall",
            "active_archetype",
            "worldpack_presentation_metadata",
        ],
        pending_constraints=pending_constraints,
        forced_transition_visible=False,
        command_boundary=command_boundary,
    )
    return ShapedTurnContract(
        category=category,
        mutation_flag=mutation_flag,
        dialogue_effect=turn_category.dialogue_effect if turn_category is not None else None,
        mode="interactive",
        allowed=True,
        forced_transition=bool(turn_category and turn_category.forced_transition),
        anti_loop_correction=bool(turn_category and (turn_category.forced or turn_category.injected_conflict)),
        anti_loop_rules_fired=list(turn_category.anti_loop_rules_fired) if turn_category is not None else [],
        required_state_delta=bool(turn_category and turn_category.state_change_required),
        discharge_target=(
            turn_category.resolved_category
            if turn_category is not None
            and turn_category.requested_category != turn_category.resolved_category
            else None
        ),
        blocked_reason=None,
        constraints=list(allowed_scope.pending_constraints),
        router_emotion=turn_category.router_emotion if turn_category is not None else None,
        allowed_scope=allowed_scope,
    )


def validate_embodied_turn(
    contract: ShapedTurnContract,
    package: OutputPackage,
    *,
    pre_state_signature: str,
    post_state_signature: str,
) -> EmbodimentValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    presentation = package.presentation
    if presentation is None or not presentation.text.strip():
        errors.append("embodiment output is empty")
    turn_summary = package.state_summary.get("turn_category", {}) or {}
    if turn_summary and turn_summary.get("resolved") != contract.category:
        errors.append("embodiment output does not match admitted category")

    if contract.mutation_flag == "non_mutating" and pre_state_signature != post_state_signature:
        errors.append("embodiment mutated state outside non-mutating contract")
    if (
        contract.mutation_flag == "mutating"
        and contract.required_state_delta
        and pre_state_signature == post_state_signature
        and not _package_contains_structural_delta(package)
    ):
        errors.append("mutating embodiment did not produce the required state delta")

    scene_characters = set(package.scene.characters)
    if not scene_characters.issubset(set(contract.allowed_scope.allowed_character_ids)):
        errors.append("embodiment introduced unauthorized scene characters")

    lumen_summary = package.state_summary.get("lumen", {}) or {}
    approved_hooks = package.state_summary.get("presentation_hooks", []) or []
    rendered_hooks = int(lumen_summary.get("rendered_hooks", 0) or 0)
    if rendered_hooks > len(approved_hooks):
        errors.append("embodiment rendered hooks outside approved presentation hooks")

    if contract.forced_transition and not contract.allowed_scope.forced_transition_visible and presentation is not None:
        lowered = presentation.text.lower()
        if any(
            marker in lowered
            for marker in (
                "forced transition",
                "forced forward motion",
                "anti-loop",
                "router",
                "reroute",
            )
        ):
            errors.append("embodiment leaked forced-transition governance into player-facing output")

    if contract.allowed_scope.command_boundary.endswith(":non_story"):
        if package.canon_update or package.memory_update or package.ending_flag:
            errors.append("non-story command boundary attempted to mutate story truth")
        if package.state_summary.get("runtime_lane") is None:
            warnings.append("non-story command boundary did not identify its runtime lane")

    return EmbodimentValidationResult(
        valid=not errors,
        blocked_commit=bool(errors),
        errors=errors,
        warnings=warnings,
    )


def _ordered_unique(values: list[str | None]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _package_contains_structural_delta(package: OutputPackage) -> bool:
    world_update = package.world_update or {}
    if package.memory_update or package.canon_update:
        return True
    if isinstance(world_update, dict):
        if world_update.get("timeline_marker"):
            return True
        if world_update.get("recent_world_events"):
            return True
        if world_update.get("flags"):
            return True
    return False
