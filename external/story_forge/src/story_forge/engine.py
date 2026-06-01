from __future__ import annotations

from dataclasses import asdict
from copy import deepcopy
from html import unescape
from pathlib import Path
import re
import shlex
from threading import Lock
from typing import TYPE_CHECKING, Any
import unicodedata
from zipfile import ZipFile

from story_forge.aris_runtime import StoryArisRuntime
from story_forge.backend_full_build import StoryForgeBackendPipeline
from story_forge.backend_import import build_backend_import_artifact
from story_forge.board_runtime import inherit_installed_boards, mount_board
from story_forge.contracts import PipelineRequest
from story_forge.debug import (
    active_event_view,
    build_runtime_status,
    canon_view,
    decision_trace_view,
    event_trace_view,
    location_history_view,
    memory_view,
    recent_event_view,
    scheduled_event_view,
    state_view,
)
from story_forge.embodiment import (
    build_shaped_turn_contract,
    validate_embodied_turn,
)
from story_forge.engine_adapter import DEFAULT_ENGINE_PROVIDER
from story_forge.llm import StoryForgeLlmRuntime
from story_forge.lumen_renderer import LumenRenderer
from story_forge.models import (
    CanonMode,
    CharacterState,
    Directive,
    Event,
    MemoryEntry,
    OutputPackage,
    Scene,
    StoryRequest,
    StoryState,
    make_id,
    utc_now,
)
from story_forge.modules import (
    assign_archetype,
    build_state_snapshot,
    generate_scene,
    package_output,
    resolve_ending,
    resolve_events,
    run_directives,
    update_canon_ledger,
    update_character_states,
    update_memory_board,
    update_world_state,
)
from story_forge.orchestrator import PipelineOrchestrator
from story_forge.persistence import load_story_state, save_story_state
from story_forge.scenario_rules import collect_scenario_progression_path
from story_forge.state_manager import (
    advance_scenario,
    apply_event_consequence,
    expire_active_events,
    get_due_scheduled_events,
    mark_scheduled_event_fired,
    register_active_event,
    schedule_event,
    tick_scenario,
)
from story_forge.system_runtime import (
    apply_collision_rules,
    resolve_system_state,
    select_admitted_actions,
)
from story_forge.turn_routing import (
    CATEGORY_CONTEXT_GATHERING,
    CATEGORY_CORRECTION_RETCON,
    CATEGORY_CREATIVE_EXPANSION,
    CATEGORY_DIRECTIVE_HOLD,
    CATEGORY_NARRATIVE_REFLECTION,
    CATEGORY_SYSTEM_META_CONTROL,
    CATEGORY_TERMINATION_EXIT,
    CATEGORY_WORLD_BUILDING,
    build_conflict_injection_event,
    build_turn_category_summary,
    classify_turn_category,
    record_turn_category,
    state_change_signature,
)
from story_forge.text_to_3d_world_lane import (
    LANE_ID as TEXT_TO_3D_WORLD_LANE_ID,
    TextTo3DOutput,
    TextTo3DWorldLane,
)
from story_forge.validation import ensure_valid_state
from story_forge.worldpacks import get_world_pack, get_world_pack_manifest
from story_forge.worldpacks.logic import (
    apply_template_to_state,
    build_memory_entries_from_pack,
    build_scene_from_template,
    event_from_template,
    loop_guard_state,
    loop_guard_summary,
    one_shot_pending_flag,
    record_template_resolution,
    refresh_ending_scores,
    resolve_world_pack_ending,
    seed_state_from_world_pack,
    select_authored_recovery_template,
    select_event_template,
    stage_entry_pending_flag,
)

if TYPE_CHECKING:
    from story_forge.movie_renderer import MovieRenderResult, MovieRenderer

TEXT_TO_3D_WORLD_LANE_ALIASES = {
    TEXT_TO_3D_WORLD_LANE_ID,
    "text_to_3d_world",
    "3d",
}
TEXT_TO_3D_WORLD_COMMAND_PREFIXES = (
    "/3d",
    "/lane 3d",
    "/lane text_to_3d_world",
    f"/lane {TEXT_TO_3D_WORLD_LANE_ID}",
)
MOVIE_RENDER_COMMAND_PREFIXES = (
    "/movie",
    "/render movie",
)
MOVIE_RENDER_STATE_ID = "movie"
MOVIE_RENDER_LEGACY_STATE_ID = "movie_renderer"
PIPELINE_COMMAND_PREFIXES = (
    "/pipeline",
    "/ingest-text",
    "/ingest_text",
)
PIPELINE_FILE_COMMAND_PREFIXES = (
    "/pipeline-file",
    "/ingest-file",
    "/ingest_file",
)
PIPELINE_STATE_ID = "frontend_pipeline"
BACKEND_IMPORT_STATE_ID = "engine_backend_import"
BACKEND_BUILD_STATE_ID = "engine_backend_build"
BRIDGE_GUARD_STATE_ID = "narrative_bridge_guard"
BRIDGE_RECENT_WINDOW = 4
BRIDGE_RECOVERY_TAG = "bridge:recovery"
BRIDGE_SINGLE_USE_TAG = "bridge:single_use"
_MOVIE_RENDER_DEFAULT_TITLE_TOKENS = {
    "render",
    "render movie",
    "render this 3d run",
    "render this run",
    "this 3d run",
    "this run",
}


class StoryForgeEngine:
    """Standalone Story Forge engine using the Jarvis v10 orchestration style."""

    ENGINE_VERSION = "v10-standalone+aris+llm"

    def __init__(
        self,
        autosave_dir: str | Path | None = None,
        artifact_dir: str | Path | None = None,
        backend_build_output_dir: str | Path | None = None,
        movie_output_dir: str | Path | None = None,
        movie_staging_dir: str | Path | None = None,
        enable_aris_runtime: bool = True,
        llm_runtime: StoryForgeLlmRuntime | None = None,
        text_to_3d_engine_provider: str = DEFAULT_ENGINE_PROVIDER,
        text_to_3d_runtime_root: str | Path | None = None,
        text_to_3d_capture_root: str | Path | None = None,
        text_to_3d_engine_command: str | list[str] | None = None,
        text_to_3d_engine_command_workdir: str | Path | None = None,
        text_to_3d_engine_timeout_seconds: float = 30.0,
        pipeline_orchestrator: PipelineOrchestrator | None = None,
    ) -> None:
        self._sessions: dict[str, StoryState] = {}
        self._lock = Lock()
        self.autosave_dir = Path(autosave_dir) if autosave_dir else None
        self.aris_runtime = StoryArisRuntime() if enable_aris_runtime else None
        self.llm_runtime = llm_runtime
        self.lumen_renderer = LumenRenderer()
        self.backend_build_pipeline = StoryForgeBackendPipeline(output_root=backend_build_output_dir)
        self._movie_output_dir = movie_output_dir
        self._movie_staging_dir = movie_staging_dir
        self._movie_renderer = None
        if pipeline_orchestrator is not None:
            self.pipeline_orchestrator = pipeline_orchestrator
        elif self.llm_runtime is not None:
            self.pipeline_orchestrator = PipelineOrchestrator(
                translation_lane=self.llm_runtime.build_translation_lane()
            )
        else:
            self.pipeline_orchestrator = PipelineOrchestrator()
        self.text_to_3d_world_lane = TextTo3DWorldLane(
            engine_provider=text_to_3d_engine_provider,
            engine_runtime_root=text_to_3d_runtime_root,
            engine_capture_root=text_to_3d_capture_root,
            engine_command=text_to_3d_engine_command,
            engine_command_workdir=text_to_3d_engine_command_workdir,
            engine_timeout_seconds=text_to_3d_engine_timeout_seconds,
        )

    def get_or_create_session(
        self,
        player_id: str,
        session_id: str | None = None,
        canon_mode: CanonMode = CanonMode.FIXED,
        world_pack_id: str | None = None,
    ) -> StoryState:
        with self._lock:
            if session_id and session_id in self._sessions:
                state = self._sessions[session_id]
                if world_pack_id and not state.world_pack_id:
                    self._load_world_pack_into_state(state, world_pack_id)
                return self._sessions[session_id]

            story_state = StoryState(
                session_id=session_id or make_id("story"),
                player_id=player_id,
                engine_version=self.ENGINE_VERSION,
                world_pack_id=world_pack_id,
                canon_mode=canon_mode,
            )
            if world_pack_id:
                self._load_world_pack_into_state(story_state, world_pack_id)
            self._sessions[story_state.session_id] = story_state
            return story_state

    def get_session(self, session_id: str) -> StoryState | None:
        with self._lock:
            return self._sessions.get(session_id)

    def add_character(self, session_id: str, character: CharacterState) -> CharacterState:
        state = self._require_session(session_id)
        state.characters[character.character_id] = character
        state.updated_at = utc_now()
        return character

    def add_directive(self, session_id: str, directive: Directive) -> Directive:
        state = self._require_session(session_id)
        state.directives.append(directive)
        state.updated_at = utc_now()
        return directive

    def start_world_pack_session(
        self,
        player_id: str,
        world_pack_id: str,
        session_id: str | None = None,
        canon_mode: CanonMode = CanonMode.FIXED,
    ) -> StoryState:
        return self.get_or_create_session(
            player_id=player_id,
            session_id=session_id,
            canon_mode=canon_mode,
            world_pack_id=world_pack_id,
        )

    def load_world_pack(self, session_id: str, world_pack_id: str) -> StoryState:
        state = self._require_session(session_id)
        if state.world_pack_id == world_pack_id:
            return state
        if state.world_pack_id and state.world_pack_id != world_pack_id:
            raise ValueError(
                "Cannot load a different world pack into an active session. "
                "Use swap_world_pack() or start_world_pack_session() to start a clean pack-aligned session."
            )
        if self._session_has_runtime_content(state):
            raise ValueError(
                "Cannot mount a world pack into a non-empty session. "
                "Start a clean world-pack session instead."
            )
        self._load_world_pack_into_state(state, world_pack_id)
        self._save_session(state)
        return state

    def swap_world_pack(
        self,
        session_id: str,
        world_pack_id: str,
        *,
        new_session_id: str | None = None,
    ) -> StoryState:
        state = self._require_session(session_id)
        swapped = self.start_world_pack_session(
            player_id=state.player_id,
            world_pack_id=world_pack_id,
            session_id=new_session_id,
            canon_mode=state.canon_mode,
        )
        inherit_installed_boards(state, swapped)
        mount_board(swapped, world_pack_id)
        self._save_session(swapped)
        return swapped

    def process_turn(self, request: StoryRequest) -> OutputPackage:
        """Run the standalone Story Forge core loop.

        Steps:
        1. INPUT      - receive player input and resolve session
        2. SNAPSHOT   - build a normalized state view
        3. DIRECTIVES - apply designer pressure and forced events
        4. UPDATE     - resolve events into world, memory, canon, and character state
        5. PACKAGE    - generate scene, image hooks, ending, and runtime output
        """
        committed_state = self.get_or_create_session(request.player_id, request.session_id)
        state = deepcopy(committed_state)
        request, input_boundary_issue = self._normalize_request(state, request)
        if input_boundary_issue is not None:
            return self._build_input_boundary_output(state, input_boundary_issue)
        request, pipeline_requested, pipeline_spec = self._resolve_pipeline_request(request)
        if pipeline_requested:
            ensure_valid_state(state)
            return self._process_pipeline_request(state, request, pipeline_spec)
        request, movie_requested, movie_title = self._resolve_movie_request(request)
        if movie_requested:
            ensure_valid_state(state)
            return self._process_movie_render_request(state, request, movie_title)
        request, requested_lane = self._resolve_lane_request(state, request)
        turn_category = None
        if requested_lane is None:
            turn_category = classify_turn_category(state, request)
            if turn_category.route == "utility":
                return self._build_turn_category_output(state, request, turn_category)
            story_metadata = dict(request.metadata)
            story_metadata["turn_category_requested"] = turn_category.requested_category
            story_metadata["turn_category_resolved"] = turn_category.resolved_category
            story_metadata["turn_category_forced"] = turn_category.forced
            story_metadata["turn_category_injected_conflict"] = turn_category.injected_conflict
            request = StoryRequest(
                player_id=request.player_id,
                player_input=request.player_input,
                session_id=request.session_id,
                choice_id=request.choice_id,
                metadata=story_metadata,
            )
        ensure_valid_state(state)
        pre_state_signature = state_change_signature(state)
        tick_scenario(state)
        expired_event_ids = expire_active_events(state, state.turn_count)
        self._schedule_expiry_followups(state, expired_event_ids)
        due_scheduled = get_due_scheduled_events(state, state.turn_count)

        reasoning_trace: list[str] = []
        if turn_category is not None:
            reasoning_trace.append(
                f"turn category: {turn_category.requested_category} -> {turn_category.resolved_category}"
            )
        if expired_event_ids:
            reasoning_trace.append(f"expired active events: {', '.join(expired_event_ids)}")
        if due_scheduled:
            reasoning_trace.append(
                f"due scheduled events: {', '.join(event.scheduled_id for event in due_scheduled)}"
            )
        aris_decision = None
        if self.aris_runtime is not None:
            aris_decision = self.aris_runtime.review_turn(state, request)
            reasoning_trace.extend(aris_decision.trace)
            if not aris_decision.allowed:
                state.updated_at = utc_now()
                package = self.aris_runtime.build_blocked_output(state, request, aris_decision)
                package.state_summary["llm"] = {
                    "requested": self.llm_runtime is not None and self.llm_runtime.requested,
                    "configured": (
                        self.llm_runtime is not None
                        and self.llm_runtime.translation_provider is not None
                    ),
                    "mode": "translation_only",
                    "provider": "skipped:story_turn",
                    "approved": False,
                    "degraded": False,
                }
                package.state_summary["llm_history_entries"] = len(state.llm_history)
                ensure_valid_state(state)
                self._save_session(state)
                self._autosave_if_configured(state)
                return package
        if requested_lane == TEXT_TO_3D_WORLD_LANE_ID:
            return self._process_text_to_3d_turn(state, request, aris_decision)
        world_pack = get_world_pack(state.world_pack_id) if state.world_pack_id else None

        snapshot = build_state_snapshot(state)
        reasoning_trace.append(
            f"snapshot built with {len(snapshot.characters)} characters, "
            f"{len(snapshot.memory_entries)} memories, and {len(snapshot.canon_entries)} canon entries"
        )

        directive_result = run_directives(state, snapshot)
        reasoning_trace.append(
            f"directive pass yielded {len(directive_result.actions)} actions and "
            f"{len(directive_result.forced_events)} forced events"
        )
        scheduled_forced_events = [
            self._scheduled_event_to_forced_event(event)
            for event in due_scheduled
        ]
        forced_events = list(directive_result.forced_events) + scheduled_forced_events
        if turn_category is not None and turn_category.injected_conflict:
            forced_events.append(build_conflict_injection_event(state, turn_category))
            reasoning_trace.append("router injected conflict to break stalled progression")

        selected_template = None
        if world_pack:
            bridge_pending = self._bridge_guard_pending(state)
            selected_template = select_event_template(world_pack, state, request)
            if selected_template is None:
                selected_template = select_authored_recovery_template(world_pack, state, request)
                if selected_template is not None:
                    reasoning_trace.append(
                        f"selected authored recovery template {selected_template.template_id}"
                    )
            reasoning_trace.extend(resolve_system_state(world_pack, state, request, selected_template))
            if selected_template:
                if bridge_pending:
                    self._clear_bridge_guard(
                        state,
                        reason=f"resolved via authored template {selected_template.template_id}",
                    )
                    reasoning_trace.append("bridge recovery discharged into authored progression")
                events = forced_events + [
                    event_from_template(
                        selected_template,
                        current_location_id=(
                            state.player_state.current_location_id or world_pack.start_location_id
                        ),
                    )
                ]
                reasoning_trace.append(f"selected world-pack template {selected_template.template_id}")
            elif forced_events:
                if bridge_pending:
                    self._clear_bridge_guard(
                        state,
                        reason="resolved via concrete forced consequence",
                    )
                    reasoning_trace.append("bridge recovery discharged into concrete forced consequence")
                events = list(forced_events)
                reasoning_trace.append(
                    "no authored template matched; concrete forced consequence used before generic recovery"
                )
            else:
                bridge_signature = self._bridge_signature(state, request)
                if bridge_pending:
                    return self._build_bridge_guard_output(
                        state,
                        request,
                        reason=(
                            "No authored aftermath, concrete consequence scene, or ending path "
                            "was available after the bridge state."
                        ),
                        bridge_signature=bridge_signature,
                    )
                if self._bridge_signature_recently_used(state, bridge_signature):
                    return self._build_bridge_guard_output(
                        state,
                        request,
                        reason=(
                            "Generic recovery narration is blocked in the recent runtime window. "
                            "The selector must land authored fallout or halt truthfully."
                        ),
                        bridge_signature=bridge_signature,
                    )
                events = self._build_bridge_recovery_events(state, request, snapshot, forced_events)
                reasoning_trace.append(
                    "no authored recovery template available; emitted single-use bridge recovery"
                )
        else:
            events = resolve_events(request, snapshot, forced_events)

        for scheduled_event in due_scheduled:
            mark_scheduled_event_fired(state, scheduled_event.scheduled_id)
        if due_scheduled:
            reasoning_trace.append(
                f"fired scheduled events: {', '.join(event.scheduled_id for event in due_scheduled)}"
            )

        durable_events = [event for event in events if not self._is_bridge_event(event)]

        for event in durable_events:
            if event.impact_level >= 2:
                register_active_event(
                    state=state,
                    event_id=event.event_id,
                    event_type=event.event_type,
                    current_turn=state.turn_count,
                    source="engine",
                )
        reasoning_trace.append(f"resolved {len(events)} event(s): {', '.join(event.event_type for event in events)}")

        state.world_state, world_update = update_world_state(state, durable_events, directive_result.actions)
        state.memory_board, memory_update = update_memory_board(state, request, durable_events)
        state.canon_ledger, canon_update = update_canon_ledger(state, durable_events, directive_result.actions)
        state.characters = update_character_states(state, durable_events, state.memory_board, state.world_state)
        state.recent_events.extend(events)
        state.recent_events = state.recent_events[-12:]
        if world_pack and selected_template:
            apply_template_to_state(state, selected_template)
            loop_report = record_template_resolution(state, selected_template)
            if loop_report["locked"]:
                reasoning_trace.append(
                    f"loop guard locked major beat {loop_report['template_id']} for the current path"
                )
            if loop_report["escalation_armed"]:
                repeat_memory = MemoryEntry(
                    entry_id=make_id("memory"),
                    memory_type="repeat_pressure",
                    weight=0.87,
                    emotional_tag="dread",
                    related_characters=list(selected_template.participants),
                    summary=(
                        f"The story recognizes the repeated pattern around {selected_template.title} "
                        "and refuses to let it land the same way again."
                    ),
                )
                reasoning_trace.append(
                    f"loop guard escalation armed after repeat pressure in stage {state.scenario_position.current_stage}"
                )
                state.memory_board.append(repeat_memory)
                state.memory_board.sort(key=lambda entry: entry.weight, reverse=True)
                state.memory_board = state.memory_board[:50]
                memory_update.append(repeat_memory)
        for event in durable_events:
            apply_event_consequence(state, event, state.turn_count)
        if world_pack and selected_template:
            reasoning_trace.extend(apply_collision_rules(world_pack, state, state.turn_count))
            pack_memory = build_memory_entries_from_pack(world_pack, state, selected_template, request)
            if pack_memory:
                state.memory_board.extend(pack_memory)
                state.memory_board.sort(key=lambda entry: entry.weight, reverse=True)
                state.memory_board = state.memory_board[:50]
                memory_update.extend(pack_memory)
            refresh_ending_scores(state)
            self._apply_world_pack_runtime_pressure(state, world_pack.pack_id)
        progression_path = collect_scenario_progression_path(state)
        progressed_to_stage = None
        for next_stage in progression_path:
            advance_scenario(state, next_stage, state.turn_count)
            reasoning_trace.append(f"scenario advanced to stage {next_stage}")
            progressed_to_stage = next_stage
        if progressed_to_stage is not None:
            state.world_state.environment_flags = [
                flag
                for flag in state.world_state.environment_flags
                if not str(flag).startswith("stage_entry_pending_")
            ]
            pending_flag = stage_entry_pending_flag(progressed_to_stage)
            should_arm_stage_entry = (
                world_pack is not None
                and any(
                    pending_flag in template.required_world_flags
                    for template in world_pack.event_templates
                )
            )
            if should_arm_stage_entry and pending_flag not in state.world_state.environment_flags:
                state.world_state.environment_flags.append(pending_flag)
                reasoning_trace.append(f"stage entry escalation armed for {progressed_to_stage}")
        state.active_archetype = assign_archetype(
            state.memory_board,
            player_intent=request.player_input,
            world_pack_id=state.world_pack_id,
            decision_trace=[*state.decision_trace, request.player_input],
        )

        state.turn_count += 1
        state.progress += 1
        state.event_trace.extend(event.outcome for event in events)
        state.decision_trace.append(request.player_input)

        fresh_snapshot = build_state_snapshot(state)
        scene = (
            build_scene_from_template(world_pack, state, selected_template)
            if world_pack and selected_template
            else generate_scene(fresh_snapshot, state.recent_events, state.active_archetype)
        )
        generic_ending = resolve_ending(state, directive_result.actions)
        ending = generic_ending
        if world_pack:
            pack_ready_flags = {
                "gate_reached",
                "crown_claimed",
                "gate_sealed",
                "nightless_secret",
                "final_confrontation",
            }
            pack_ready = (
                generic_ending is not None
                or state.scenario_position.current_stage in {"endgame", "aftermath"}
                or any(flag in state.world_state.environment_flags for flag in pack_ready_flags)
            )
            if pack_ready:
                pack_ending = resolve_world_pack_ending(world_pack, state)
                if pack_ending is not None:
                    ending = pack_ending
                elif state.scenario_position.current_stage in {"endgame", "aftermath"} or any(
                    flag in state.world_state.environment_flags for flag in pack_ready_flags
                ):
                    ending = generic_ending
                else:
                    ending = None
        image_prompt = None
        visual_recall_summary = {
            "triggered": False,
            "artifact_ids": [],
            "hooks": [],
            "symbols": [],
            "match_reasons": [],
            "context": "",
            "disabled": True,
        }
        visual_artifact_summary: dict[str, object] = {
            "stored": False,
            "disabled": True,
        }
        visual_memory_summary = {
            "artifact_count": 0,
            "hook_count": 0,
            "pending_recall": False,
            "pending_hooks": [],
            "last_recall_artifact_ids": [],
            "disabled": True,
        }
        reasoning_trace.append("image generation disabled: live image prompt path removed")

        state.last_scene = scene
        state.current_ending = ending
        state.updated_at = utc_now()

        package = package_output(
            state=state,
            scene=scene,
            world_update=world_update,
            memory_update=memory_update,
            canon_update=canon_update,
            image_prompt=image_prompt,
            ending=ending,
            reasoning_trace=reasoning_trace,
        )
        package.state_summary["visual_recall"] = visual_recall_summary
        package.state_summary["visual_artifact"] = visual_artifact_summary
        package.state_summary["visual_memory"] = visual_memory_summary
        package.state_summary["presentation_hooks"] = []
        if world_pack:
            action_selection = select_admitted_actions(world_pack, state, request, selected_template)
            package.state_summary["action_selection"] = {
                "primary_action_id": action_selection.primary_action_id,
                "support_action_ids": list(action_selection.support_action_ids),
                "trace": list(action_selection.trace),
            }
            package.state_summary["system_state"] = {
                "active_system": state.system_state.active_system,
                "secondary_system": state.system_state.secondary_system,
                "collision_mode": state.system_state.collision_mode,
                "last_collision_signature": state.system_state.last_collision_signature,
            }
            package.state_summary["loop_guard"] = loop_guard_summary(state)
            package.state_summary["bridge_guard"] = self._bridge_guard_summary(state)
        package.state_summary["llm"] = {
            "requested": self.llm_runtime is not None and self.llm_runtime.requested,
            "configured": (
                self.llm_runtime is not None
                and self.llm_runtime.translation_provider is not None
            ),
            "mode": "translation_only",
            "provider": "skipped:story_turn",
            "approved": False,
            "degraded": False,
        }
        package.state_summary["llm_history_entries"] = len(state.llm_history)
        state_changed = pre_state_signature != state_change_signature(state)
        if turn_category is not None and turn_category.state_change_required and not state_changed:
            reasoning_trace.append(
                "turn routing law: requested forward motion did not change state; pressure counter increased"
            )
        if turn_category is not None:
            record_turn_category(
                state,
                request,
                turn_category,
                story_mutated=True,
                state_changed=state_changed,
            )
            package.state_summary["turn_category"] = turn_category.to_payload()
            package.state_summary["turn_router"] = build_turn_category_summary(state)
        shaped_turn_contract = build_shaped_turn_contract(
            state,
            request,
            turn_category,
            scene,
            events,
            requested_lane=requested_lane,
        )
        package.state_summary["shaped_turn_contract"] = shaped_turn_contract.to_payload()
        package = self.lumen_renderer.render(state, request, package)
        embodiment_validation = validate_embodied_turn(
            shaped_turn_contract,
            package,
            pre_state_signature=pre_state_signature,
            post_state_signature=state_change_signature(state),
        )
        package.state_summary["embodiment_validation"] = embodiment_validation.to_payload()
        self._record_embodiment_validation(
            state,
            request,
            shaped_turn_contract.to_payload(),
            embodiment_validation.to_payload(),
        )
        if not embodiment_validation.valid:
            return self._build_embodiment_rejection_output(
                committed_state,
                request,
                shaped_turn_contract.to_payload(),
                embodiment_validation.to_payload(),
            )
        if self.aris_runtime is not None and aris_decision is not None:
            self.aris_runtime.commit_turn(state, request, package, aris_decision)

        ensure_valid_state(state)
        self._save_session(state)
        self._autosave_if_configured(state)
        return package

    def _apply_world_pack_runtime_pressure(self, state: StoryState, world_pack_id: str) -> None:
        if world_pack_id != "velvet_system":
            return
        if state.scenario_position.current_stage not in {"opening", "threads"}:
            return

        world_flags = set(state.world_state.environment_flags)
        if "syntax_touched" in world_flags:
            return
        if not {"confession_carried", "oath_threaded"}.issubset(world_flags):
            return

        if int(loop_guard_state(state).get("repeat_pressure", 0) or 0) > 0:
            pending_flag = one_shot_pending_flag("velvet_threads_escalation")
            if pending_flag not in state.world_state.environment_flags:
                state.world_state.environment_flags.append(pending_flag)
            return

        loop_locations = {"velvet_knife_street", "confession_chamber", "old_moor"}
        recent_loop_visits = [
            transition.to_location
            for transition in state.location_history[-4:]
            if transition.to_location in loop_locations
        ]
        if len(recent_loop_visits) < 4:
            return
        if len(set(recent_loop_visits)) < 2:
            return
        if all(recent_loop_visits.count(location_id) < 2 for location_id in set(recent_loop_visits)):
            return

        pending_flag = one_shot_pending_flag("velvet_threads_escalation")
        if pending_flag not in state.world_state.environment_flags:
            state.world_state.environment_flags.append(pending_flag)

    def _bridge_guard_state(self, state: StoryState) -> dict[str, Any]:
        lane = state.runtime_lanes.get(BRIDGE_GUARD_STATE_ID, {})
        if not isinstance(lane, dict):
            return {}
        return lane

    def _bridge_guard_pending(self, state: StoryState) -> bool:
        return bool(self._bridge_guard_state(state).get("pending", False))

    def _bridge_signature(self, state: StoryState, request: StoryRequest) -> str:
        category = str(request.metadata.get("turn_category_resolved", "choice") or "choice").strip().lower()
        location_id = str(state.player_state.current_location_id or "unknown").strip().lower()
        stage = str(state.scenario_position.current_stage or "opening").strip().lower()
        pack_id = str(state.world_pack_id or "default").strip().lower()
        return f"{pack_id}:{stage}:{location_id}:{category}"

    def _bridge_signature_recently_used(self, state: StoryState, bridge_signature: str) -> bool:
        history = self._bridge_guard_state(state).get("history", [])
        if not isinstance(history, list):
            return False
        recent_signatures = [
            str(entry.get("signature", "")).strip()
            for entry in history[-BRIDGE_RECENT_WINDOW:]
            if isinstance(entry, dict)
        ]
        return bridge_signature in recent_signatures

    def _bridge_guard_summary(self, state: StoryState) -> dict[str, Any]:
        lane = self._bridge_guard_state(state)
        history = lane.get("history", [])
        if not isinstance(history, list):
            history = []
        recent_history = [
            {
                "signature": str(entry.get("signature", "")).strip(),
                "reason": str(entry.get("reason", "")).strip(),
                "blocked": bool(entry.get("blocked", False)),
            }
            for entry in history[-BRIDGE_RECENT_WINDOW:]
            if isinstance(entry, dict)
        ]
        return {
            "pending": bool(lane.get("pending", False)),
            "pending_signature": str(lane.get("pending_signature", "") or ""),
            "recent_history": recent_history,
            "last_reason": str(lane.get("last_reason", "") or ""),
        }

    def _clear_bridge_guard(self, state: StoryState, *, reason: str) -> None:
        lane = dict(self._bridge_guard_state(state))
        lane["pending"] = False
        lane["pending_signature"] = ""
        lane["last_reason"] = reason
        lane["updatedAt"] = utc_now()
        state.runtime_lanes[BRIDGE_GUARD_STATE_ID] = lane

    def _is_bridge_event(self, event: Event) -> bool:
        return any(str(tag).startswith("bridge:") for tag in event.tags)

    def _build_bridge_recovery_events(
        self,
        state: StoryState,
        request: StoryRequest,
        snapshot,
        forced_events: list[Event],
    ) -> list[Event]:
        bridge_signature = self._bridge_signature(state, request)
        events = resolve_events(request, snapshot, forced_events)
        bridge_event = events[-1]
        bridge_event.tags = list(
            dict.fromkeys(
                [
                    *bridge_event.tags,
                    BRIDGE_RECOVERY_TAG,
                    BRIDGE_SINGLE_USE_TAG,
                    f"bridge_signature:{bridge_signature}",
                ]
            )
        )

        lane = dict(self._bridge_guard_state(state))
        history = lane.get("history", [])
        if not isinstance(history, list):
            history = []
        history.append(
            {
                "signature": bridge_signature,
                "reason": "bridge_recovery_emitted",
                "blocked": False,
                "outcome": bridge_event.outcome,
                "timestamp": utc_now(),
            }
        )
        lane["history"] = history[-BRIDGE_RECENT_WINDOW:]
        lane["pending"] = True
        lane["pending_signature"] = bridge_signature
        lane["last_reason"] = "bridge_recovery_emitted"
        lane["updatedAt"] = utc_now()
        state.runtime_lanes[BRIDGE_GUARD_STATE_ID] = lane
        return events

    def _build_bridge_guard_output(
        self,
        state: StoryState,
        request: StoryRequest,
        *,
        reason: str,
        bridge_signature: str,
    ) -> OutputPackage:
        lane = dict(self._bridge_guard_state(state))
        history = lane.get("history", [])
        if not isinstance(history, list):
            history = []
        history.append(
            {
                "signature": bridge_signature,
                "reason": reason,
                "blocked": True,
                "timestamp": utc_now(),
            }
        )
        lane["history"] = history[-BRIDGE_RECENT_WINDOW:]
        lane["pending"] = False
        lane["pending_signature"] = ""
        lane["last_reason"] = reason
        lane["updatedAt"] = utc_now()
        state.runtime_lanes[BRIDGE_GUARD_STATE_ID] = lane
        state.updated_at = utc_now()

        scene = Scene(
            text=(
                "Recovery bridge blocked before it could become a durable loop.\n"
                f"{reason}"
            ),
            characters=list(state.last_scene.characters) if state.last_scene is not None else ["Bridge Guard"],
            choices=list(state.last_scene.choices) if state.last_scene is not None else ["Continue with a governed turn request."],
            tone=state.last_scene.tone if state.last_scene is not None else "steady",
            consequence_tags=["utility:bridge_guard", "commit:blocked"],
        )
        package = package_output(
            state=state,
            scene=scene,
            world_update={},
            memory_update=[],
            canon_update=[],
            image_prompt=None,
            ending=None,
            reasoning_trace=[
                "bridge guard blocked repeated generic recovery",
                reason,
            ],
        )
        package.state_summary["bridge_guard"] = self._bridge_guard_summary(state)
        package.state_summary["llm"] = {
            "requested": self.llm_runtime is not None and self.llm_runtime.requested,
            "configured": (
                self.llm_runtime is not None
                and self.llm_runtime.translation_provider is not None
            ),
            "mode": "translation_only",
            "provider": "skipped:story_turn",
            "approved": False,
            "degraded": False,
        }
        package.state_summary["llm_history_entries"] = len(state.llm_history)
        package.state_summary["lumen"] = {
            "mode": "skipped",
            "persona": "LUMEN",
            "cartridge": getattr(state, "world_pack_id", None) or "none",
            "version": self.lumen_renderer.version,
            "style_source": "skipped:bridge_guard",
            "rendered_visual_recall": False,
            "rendered_hooks": 0,
            "request_text": request.player_input,
        }
        if self.aris_runtime is not None:
            package.state_summary["aris_runtime"] = self.aris_runtime.summary(state)
        self._save_session(state)
        self._autosave_if_configured(state)
        return package

    def _process_text_to_3d_turn(
        self,
        state: StoryState,
        request: StoryRequest,
        aris_decision: Any | None,
    ) -> OutputPackage:
        lane_entry = self._lane_entry(state, TEXT_TO_3D_WORLD_LANE_ID)
        prior_state = self._text_to_3d_prior_state(lane_entry)
        world_id = lane_entry.get("worldId") if isinstance(lane_entry.get("worldId"), str) else None
        lane_output = self.text_to_3d_world_lane.run(
            {
                "lane": TEXT_TO_3D_WORLD_LANE_ID,
                "text": request.player_input,
                "sessionId": state.session_id,
                "worldId": world_id,
                "priorState": prior_state,
            }
        )

        self._persist_text_to_3d_output(state, lane_output, request.player_input)

        state.turn_count += 1
        state.progress += 1
        state.event_trace.extend(
            (
                "text_to_3d:"
                f"{event.get('type', 'event')}:"
                f"{event.get('transitionId', event.get('eventId', 'unknown'))}"
            )
            for event in lane_output.event_records
        )
        state.decision_trace.append(request.player_input)

        scene = self._build_text_to_3d_scene(lane_output)
        state.last_scene = scene
        state.current_ending = None
        state.updated_at = utc_now()

        reasoning_trace = [
            f"runtime lane dispatched: {TEXT_TO_3D_WORLD_LANE_ID}",
            f"world id: {lane_output.world_id}",
            f"scene graph handle: {lane_output.scene_graph_handle}",
            (
                "runtime step advanced to "
                f"tick {lane_output.game_state.get('tick', 0)} "
                f"with narrative score {lane_output.game_state.get('narrativeScore', 0)}"
            ),
        ]

        package = package_output(
            state=state,
            scene=scene,
            world_update={},
            memory_update=[],
            canon_update=[],
            image_prompt=None,
            ending=None,
            reasoning_trace=reasoning_trace,
        )
        location_anchor = lane_output.scene_spec.get("locationAnchor", {})
        package.state_summary["runtime_lane"] = TEXT_TO_3D_WORLD_LANE_ID
        package.state_summary["text_to_3d_world"] = {
            "engine_provider": self.text_to_3d_world_lane.engine_module.provider_name,
            "world_id": lane_output.world_id,
            "scene_graph_handle": lane_output.scene_graph_handle,
            "tick": int(lane_output.game_state.get("tick", 0) or 0),
            "narrative_score": int(lane_output.game_state.get("narrativeScore", 0) or 0),
            "location_anchor": str(location_anchor.get("id", "threshold") or "threshold"),
            "theme": str(lane_output.scene_spec.get("theme", "")),
            "mood": str(lane_output.scene_spec.get("mood", "")),
            "event_ids": [
                str(event.get("eventId", ""))
                for event in lane_output.event_records
                if str(event.get("eventId", "")).strip()
            ],
        }
        package.state_summary["presentation_hooks"] = []
        package.state_summary["llm"] = {
            "requested": self.llm_runtime is not None and self.llm_runtime.requested,
            "configured": (
                self.llm_runtime is not None
                and self.llm_runtime.translation_provider is not None
            ),
            "mode": "translation_only",
            "provider": "skipped:text_to_3d_world",
            "approved": False,
            "degraded": False,
        }
        package.state_summary["llm_history_entries"] = len(state.llm_history)
        package.state_summary["lumen"] = {
            "mode": "skipped",
            "persona": "LUMEN",
            "cartridge": getattr(state, "world_pack_id", None) or "none",
            "version": self.lumen_renderer.version,
            "style_source": "skipped:text_to_3d_world",
            "rendered_visual_recall": False,
            "rendered_hooks": 0,
            "request_text": request.player_input,
        }

        if self.aris_runtime is not None and aris_decision is not None:
            self.aris_runtime.commit_turn(state, request, package, aris_decision)

        ensure_valid_state(state)
        self._save_session(state)
        self._autosave_if_configured(state)
        return package

    def get_state_summary(self, session_id: str) -> dict[str, Any]:
        return state_view(self._require_session(session_id))

    def get_memory_summary(self, session_id: str) -> list[dict[str, object]]:
        return memory_view(self._require_session(session_id))

    def get_canon_summary(self, session_id: str) -> list[dict[str, object]]:
        return canon_view(self._require_session(session_id))

    def get_aris_summary(self, session_id: str) -> dict[str, object]:
        state = self._require_session(session_id)
        if self.aris_runtime is None:
            return {}
        return self.aris_runtime.summary(state)

    def get_debug_views(self, session_id: str) -> dict[str, Any]:
        state = self._require_session(session_id)
        return {
            "state": state_view(state),
            "runtime_status": build_runtime_status(state),
            "memory": memory_view(state),
            "canon": canon_view(state),
            "recent_events": recent_event_view(state),
            "active_events": active_event_view(state),
            "scheduled_events": scheduled_event_view(state),
            "location_history": location_history_view(state),
            "event_trace": event_trace_view(state),
            "decision_trace": decision_trace_view(state),
            "llm_history": list(state.llm_history),
            "runtime_lanes": deepcopy(state.runtime_lanes),
            "visual_memory": self.visual_recall_engine.memory_summary(state),
            "aris": self.get_aris_summary(session_id),
        }

    def clear_session_history(self, session_id: str) -> dict[str, str]:
        state = self._require_session(session_id)
        reset_state = self._fresh_session_state(
            session_id=state.session_id,
            player_id=state.player_id,
            canon_mode=state.canon_mode,
            runtime_mode=state.runtime_mode,
            world_pack_id=state.world_pack_id,
            created_at=state.created_at,
        )
        self._save_session(reset_state)
        return {"status": "reset", "session_id": session_id}

    def _lane_entry(self, state: StoryState, lane_id: str) -> dict[str, Any]:
        lane_state = state.runtime_lanes.get(lane_id, {})
        return lane_state if isinstance(lane_state, dict) else {}

    def _text_to_3d_prior_state(self, lane_entry: dict[str, Any]) -> dict[str, Any] | None:
        prior_state = lane_entry.get("priorState")
        if not isinstance(prior_state, dict):
            return None
        return deepcopy(prior_state)

    def _persist_text_to_3d_output(
        self,
        state: StoryState,
        lane_output: TextTo3DOutput,
        request_text: str,
    ) -> None:
        prior_lane_state = self._lane_entry(state, TEXT_TO_3D_WORLD_LANE_ID)
        history_raw = prior_lane_state.get("history", [])
        history: list[dict[str, Any]] = []
        if isinstance(history_raw, list):
            for entry in history_raw:
                if isinstance(entry, dict):
                    history.append(dict(entry))
        history.append(
            {
                "requestText": request_text,
                "output": lane_output.to_payload(),
                "updatedAt": utc_now(),
            }
        )
        history = history[-50:]
        state.runtime_lanes[TEXT_TO_3D_WORLD_LANE_ID] = {
            "worldId": lane_output.world_id,
            "engineProvider": self.text_to_3d_world_lane.engine_module.provider_name,
            "priorState": {
                "sceneSpec": deepcopy(lane_output.scene_spec),
                "sceneGraphHandle": lane_output.scene_graph_handle,
                "gameState": deepcopy(lane_output.game_state),
                "eventRecords": deepcopy(lane_output.event_records),
                "nextText": lane_output.next_text,
            },
            "lastOutput": lane_output.to_payload(),
            "lastRequestText": request_text,
            "history": history,
            "updatedAt": utc_now(),
        }

    def _build_text_to_3d_scene(self, lane_output: TextTo3DOutput) -> Scene:
        location_anchor = lane_output.scene_spec.get("locationAnchor", {})
        location_label = str(location_anchor.get("label", "Threshold") or "Threshold")
        location_id = str(location_anchor.get("id", "threshold") or "threshold")
        theme = str(lane_output.scene_spec.get("theme", "mythic_threshold") or "mythic_threshold")
        mood = str(lane_output.scene_spec.get("mood", "steady") or "steady")
        focal_labels = [
            str(item.get("label", "")).strip()
            for item in lane_output.scene_spec.get("focalObjects", [])
            if isinstance(item, dict) and str(item.get("label", "")).strip()
        ]
        text_lines = [
            lane_output.next_text or str(lane_output.scene_spec.get("summary", "The scene reformats around a stable anchor.")),
            (
                f"Anchor: {location_label} | "
                f"Theme: {theme.replace('_', ' ')} | "
                f"Mood: {mood}"
            ),
            (
                f"Scene graph: {lane_output.scene_graph_handle} | "
                f"Tick: {lane_output.game_state.get('tick', 0)} | "
                f"Narrative score: {lane_output.game_state.get('narrativeScore', 0)}"
            ),
        ]
        if focal_labels:
            text_lines.append("Focal objects: " + ", ".join(focal_labels[:4]))

        primary_focus = focal_labels[0].lower() if focal_labels else "the nearest structure"
        choices = [
            f"/3d inspect {primary_focus}",
            f"/3d move deeper into {location_label.lower()}",
            "/3d stabilize the scene and observe the next transition",
            "/movie",
        ]
        return Scene(
            text="\n".join(text_lines),
            characters=focal_labels[:3] or [location_label],
            choices=choices,
            tone=mood,
            consequence_tags=[
                f"lane:{TEXT_TO_3D_WORLD_LANE_ID}",
                f"anchor:{location_id}",
                f"theme:{theme}",
            ],
        )

    def save_session(self, session_id: str, path: str | Path) -> Path:
        state = self._require_session(session_id)
        return save_story_state(path, state)

    def render_movie(
        self,
        session_id: str,
        *,
        title: str | None = None,
        output_dir: str | Path | None = None,
        presentation_mode: str | None = None,
    ) -> MovieRenderResult:
        state = self._require_session(session_id)
        result = self._get_movie_renderer().render_movie(
            state,
            output_dir=output_dir,
            title=title,
            presentation_mode=presentation_mode,
        )
        state.runtime_lanes[MOVIE_RENDER_STATE_ID] = self._movie_lane_payload(
            result,
            requested_title=title,
        )
        state.runtime_lanes.pop(MOVIE_RENDER_LEGACY_STATE_ID, None)
        state.updated_at = utc_now()
        self._save_session(state)
        return result

    def _get_movie_renderer(self) -> MovieRenderer:
        if self._movie_renderer is None:
            from story_forge.movie_renderer import MovieRenderer

            self._movie_renderer = MovieRenderer(
                output_root=self._movie_output_dir,
                staging_root=self._movie_staging_dir,
            )
        return self._movie_renderer

    def _movie_lane_payload(
        self,
        result: MovieRenderResult,
        *,
        requested_title: str | None,
    ) -> dict[str, Any]:
        return {
            "lastRenderId": result.render_id,
            "sourceLaneReference": TEXT_TO_3D_WORLD_LANE_ID,
            "timestamp": utc_now(),
            "outputPath": str(result.output_dir),
            "auditPath": str(result.audit_path or ""),
            "auditWitness": result.audit_witness,
            "renderParams": {
                "title": result.title,
                "requestedTitle": str(requested_title or "").strip(),
                "presentationMode": result.presentation_mode,
                "narrationSource": result.narration_source,
                "sceneCount": result.scene_count,
                "videoPath": str(result.video_path),
                "screenplayPath": str(result.screenplay_path),
                "shotListPath": str(result.shot_list_path),
                "metadataPath": str(result.metadata_path),
                "framesDir": str(result.frames_dir),
            },
        }

    def load_session(self, path: str | Path) -> StoryState:
        state = load_story_state(path)
        self._save_session(state)
        return state

    def _save_session(self, state: StoryState) -> None:
        with self._lock:
            self._sessions[state.session_id] = state

    def _autosave_if_configured(self, state: StoryState) -> None:
        if self.autosave_dir is None:
            return
        self.autosave_dir.mkdir(parents=True, exist_ok=True)
        save_story_state(self.autosave_dir / f"{state.session_id}.json", state)

    def _record_embodiment_validation(
        self,
        state: StoryState,
        request: StoryRequest,
        shaped_turn_contract: dict[str, Any],
        validation: dict[str, Any],
    ) -> None:
        lane_state = self._lane_entry(state, "lumen_embodiment")
        history = list(lane_state.get("history", []))
        history.append(
            {
                "timestamp": utc_now(),
                "turn_count": state.turn_count,
                "request_text": request.player_input,
                "category": shaped_turn_contract.get("category"),
                "mutation_flag": shaped_turn_contract.get("mutation_flag"),
                "forced_transition": bool(shaped_turn_contract.get("forced_transition", False)),
                "valid": bool(validation.get("valid", False)),
                "blocked_commit": bool(validation.get("blocked_commit", False)),
                "errors": list(validation.get("errors", [])),
                "warnings": list(validation.get("warnings", [])),
            }
        )
        state.runtime_lanes["lumen_embodiment"] = {
            "history": history[-24:],
            "last_contract": shaped_turn_contract,
            "last_validation": validation,
            "updatedAt": utc_now(),
        }

    def _build_embodiment_rejection_output(
        self,
        committed_state: StoryState,
        request: StoryRequest,
        shaped_turn_contract: dict[str, Any],
        validation: dict[str, Any],
    ) -> OutputPackage:
        state = deepcopy(committed_state)
        self._record_embodiment_validation(state, request, shaped_turn_contract, validation)
        scene = Scene(
            text=(
                "Embodiment validation blocked commit.\n"
                "The turn did not become story truth because presentation failed the shaped-turn contract."
            ),
            characters=["Embodiment Validator"],
            choices=list(state.last_scene.choices) if state.last_scene is not None else ["Continue with a governed turn request."],
            tone="steady",
            consequence_tags=["utility:embodiment_validation", "commit:blocked"],
        )
        package = package_output(
            state=state,
            scene=scene,
            world_update={},
            memory_update=[],
            canon_update=[],
            image_prompt=None,
            ending=None,
            reasoning_trace=[
                "embodiment validation blocked state commit",
                *[str(error) for error in validation.get("errors", [])],
            ],
        )
        package.state_summary["shaped_turn_contract"] = shaped_turn_contract
        package.state_summary["embodiment_validation"] = validation
        package.state_summary["llm"] = {
            "requested": self.llm_runtime is not None and self.llm_runtime.requested,
            "configured": (
                self.llm_runtime is not None
                and self.llm_runtime.translation_provider is not None
            ),
            "mode": "translation_only",
            "provider": "skipped:story_turn",
            "approved": False,
            "degraded": False,
        }
        package.state_summary["llm_history_entries"] = len(state.llm_history)
        package.state_summary["lumen"] = {
            "mode": "rejected",
            "persona": "LUMEN",
            "cartridge": getattr(state, "world_pack_id", None) or "none",
            "version": self.lumen_renderer.version,
            "style_source": "rejected:embodiment_validation",
            "rendered_visual_recall": False,
            "rendered_hooks": 0,
            "request_text": request.player_input,
        }
        if self.aris_runtime is not None:
            package.state_summary["aris_runtime"] = self.aris_runtime.summary(state)
        state.updated_at = utc_now()
        self._save_session(state)
        self._autosave_if_configured(state)
        return package

    def _fresh_session_state(
        self,
        *,
        session_id: str,
        player_id: str,
        canon_mode: CanonMode,
        runtime_mode: str,
        world_pack_id: str | None,
        created_at: str | None = None,
    ) -> StoryState:
        story_state = StoryState(
            session_id=session_id,
            player_id=player_id,
            engine_version=self.ENGINE_VERSION,
            runtime_mode=runtime_mode,
            world_pack_id=world_pack_id,
            canon_mode=canon_mode,
        )
        if created_at is not None:
            story_state.created_at = created_at
        if world_pack_id:
            self._load_world_pack_into_state(story_state, world_pack_id)
        return story_state

    def _load_world_pack_into_state(self, state: StoryState, world_pack_id: str) -> None:
        manifest = get_world_pack_manifest(world_pack_id)
        if manifest is None:
            raise ValueError(f"World pack '{world_pack_id}' is not registered.")
        world_pack = get_world_pack(world_pack_id)
        if world_pack is None:
            raise ValueError(f"World pack '{world_pack_id}' was not found.")
        seed_state_from_world_pack(state, world_pack)
        mount_board(state, world_pack_id)
        state.runtime_lanes["world_pack_boot"] = {
            "packId": manifest.pack_id,
            "boardId": manifest.board_id,
            "title": manifest.title,
            "category": manifest.category,
            "startLocationId": manifest.start_location_id,
            "requiredModules": list(manifest.required_modules),
            "optionalModules": list(manifest.optional_modules),
            "updatedAt": utc_now(),
        }
        state.world_pack_id = world_pack_id
        state.updated_at = utc_now()

    def _session_has_runtime_content(self, state: StoryState) -> bool:
        default_status = {"health": 100, "morality": 0, "power": 0}
        return any(
            [
                bool(state.world_state.locations),
                bool(state.world_state.factions),
                bool(state.world_state.environment_flags),
                bool(state.world_state.world_events),
                state.world_state.timeline_marker != 0,
                state.player_state.current_location_id != "story_hub",
                bool(state.player_state.inventory),
                bool(state.player_state.flags),
                dict(state.player_state.status) != default_status,
                bool(state.characters),
                bool(state.memory_board),
                bool(state.canon_ledger),
                bool(state.directives),
                bool(state.recent_events),
                state.active_archetype is not None,
                state.last_scene is not None,
                state.current_ending is not None,
                state.turn_count != 0,
                state.progress != 0,
                any(float(value) != 0.0 for value in state.ending_scores.values()),
                bool(state.llm_history),
                bool(state.runtime_lanes),
                bool(state.visual_memory.artifact_ids),
                bool(state.visual_memory.hook_state),
                state.visual_memory.pending_context is not None,
                bool(state.visual_memory.last_recall_artifact_ids),
                bool(state.location_history),
                bool(state.active_events),
                bool(state.scheduled_events),
                bool(state.event_trace),
                bool(state.decision_trace),
            ]
        )

    def _normalize_request(
        self,
        state: StoryState,
        request: StoryRequest,
    ) -> tuple[StoryRequest, dict[str, Any] | None]:
        player_input = request.player_input.strip()
        if not player_input:
            if state.last_scene is None:
                return request, None
            return request, {
                "reason": "empty_input",
                "message": "Enter a numbered choice or a narrative action to continue.",
                "raw_input": request.player_input,
            }
        if state.last_scene is None:
            return request, None
        if not player_input.isdigit():
            return request, None

        choice_index = int(player_input) - 1
        available_choices = len(state.last_scene.choices)
        if choice_index < 0 or choice_index >= available_choices:
            return request, {
                "reason": "invalid_choice_index",
                "message": (
                    f"Choice {player_input} is not available right now. "
                    f"Enter a number between 1 and {available_choices}, or type a new action."
                ),
                "raw_input": request.player_input,
                "available_choices": available_choices,
            }

        resolved_choice = state.last_scene.choices[choice_index]
        metadata = dict(request.metadata)
        metadata["from_scene_choice"] = True
        metadata["raw_player_input"] = request.player_input
        metadata["resolved_choice_index"] = choice_index + 1
        metadata["resolved_choice_text"] = resolved_choice
        return (
            StoryRequest(
                player_id=request.player_id,
                player_input=resolved_choice,
                session_id=request.session_id,
                choice_id=str(choice_index + 1),
                metadata=metadata,
            ),
            None,
        )

    def _build_input_boundary_output(
        self,
        state: StoryState,
        issue: dict[str, Any],
    ) -> OutputPackage:
        base_scene = state.last_scene or Scene(
            text="Enter a numbered choice or a narrative action to continue.",
            characters=[],
            choices=[],
            tone="steady",
        )
        scene = Scene(
            text=f"{issue['message']}\n\n{base_scene.text}",
            characters=list(base_scene.characters),
            choices=list(base_scene.choices),
            tone=base_scene.tone,
            consequence_tags=list(base_scene.consequence_tags) + ["input_boundary"],
        )
        package = package_output(
            state=state,
            scene=scene,
            world_update={},
            memory_update=[],
            canon_update=[],
            image_prompt=None,
            ending=state.current_ending,
            reasoning_trace=[f"input rejected at boundary: {issue['reason']}"],
        )
        package.state_summary["input_boundary"] = {
            "rejected": True,
            "reason": issue["reason"],
            "message": issue["message"],
            "raw_input": issue.get("raw_input", ""),
        }
        package.state_summary["llm"] = {
            "requested": False,
            "configured": False,
            "mode": "stability",
            "provider": "skipped:input_boundary",
            "approved": False,
            "degraded": False,
        }
        package.state_summary["llm_history_entries"] = len(state.llm_history)
        package.state_summary["lumen"] = {
            "mode": "skipped",
            "persona": "LUMEN",
            "cartridge": getattr(state, "world_pack_id", None) or "none",
            "version": self.lumen_renderer.version,
            "style_source": "skipped:input_boundary",
            "rendered_visual_recall": False,
            "rendered_hooks": 0,
        }
        if self.aris_runtime is not None:
            package.state_summary["aris_runtime"] = self.aris_runtime.summary(state)
        return package

    def _build_turn_category_output(
        self,
        state: StoryState,
        request: StoryRequest,
        turn_category,
    ) -> OutputPackage:
        record_turn_category(
            state,
            request,
            turn_category,
            story_mutated=False,
            state_changed=False,
        )
        scene = Scene(
            text=self._turn_category_scene_text(state, turn_category),
            characters=list(state.last_scene.characters) if state.last_scene is not None else [],
            choices=list(state.last_scene.choices) if state.last_scene is not None else [],
            tone=state.last_scene.tone if state.last_scene is not None else "steady",
            consequence_tags=["utility:turn_router", turn_category.resolved_category],
        )
        package = package_output(
            state=state,
            scene=scene,
            world_update={},
            memory_update=[],
            canon_update=[],
            image_prompt=None,
            ending=state.current_ending,
            reasoning_trace=[
                f"turn routed to utility category {turn_category.resolved_category}",
                *turn_category.reasons,
            ],
        )
        package.state_summary["turn_category"] = turn_category.to_payload()
        package.state_summary["turn_router"] = build_turn_category_summary(state)
        package.state_summary["llm"] = {
            "requested": self.llm_runtime is not None and self.llm_runtime.requested,
            "configured": (
                self.llm_runtime is not None
                and self.llm_runtime.translation_provider is not None
            ),
            "mode": "translation_only",
            "provider": "skipped:turn_router",
            "approved": False,
            "degraded": False,
        }
        package.state_summary["llm_history_entries"] = len(state.llm_history)
        package.state_summary["lumen"] = {
            "mode": "skipped",
            "persona": "LUMEN",
            "cartridge": getattr(state, "world_pack_id", None) or "none",
            "version": self.lumen_renderer.version,
            "style_source": "skipped:turn_router",
            "rendered_visual_recall": False,
            "rendered_hooks": 0,
        }
        if self.aris_runtime is not None:
            package.state_summary["aris_runtime"] = self.aris_runtime.summary(state)
        self._save_session(state)
        self._autosave_if_configured(state)
        return package

    def _turn_category_scene_text(self, state: StoryState, turn_category) -> str:
        current_location = state.player_state.current_location_id or "unknown"
        last_events = [event.event_type for event in state.recent_events[-3:]]
        world_flags = list(state.world_state.environment_flags[-6:])
        current_choices = list(state.last_scene.choices) if state.last_scene is not None else []

        if turn_category.resolved_category == CATEGORY_CONTEXT_GATHERING:
            return (
                f"Context gathered.\n"
                f"Location: {current_location}\n"
                f"Stage: {state.scenario_position.current_stage}\n"
                f"Recent events: {', '.join(last_events) if last_events else 'none'}\n"
                f"Open pressures: {', '.join(world_flags) if world_flags else 'none'}"
            )
        if turn_category.resolved_category == CATEGORY_NARRATIVE_REFLECTION:
            return (
                "Narrative reflection.\n"
                f"The story is currently centered on {current_location} during "
                f"{state.scenario_position.current_stage}. "
                f"Recent motion: {', '.join(last_events) if last_events else 'none yet'}."
            )
        if turn_category.resolved_category == CATEGORY_WORLD_BUILDING:
            canon_lines = [entry.description for entry in state.canon_ledger[:3]]
            return (
                "World context.\n"
                + ("\n".join(canon_lines) if canon_lines else "No canon anchors are currently loaded.")
            )
        if turn_category.resolved_category == CATEGORY_DIRECTIVE_HOLD:
            return (
                "Directive hold acknowledged.\n"
                "The story does not advance on this turn. Use a direct action or scene-forward input next."
            )
        if turn_category.resolved_category == CATEGORY_CORRECTION_RETCON:
            return (
                "Correction lane.\n"
                "Retcon and correction requests are treated as governance proposals, not live story mutation."
            )
        if turn_category.resolved_category == CATEGORY_SYSTEM_META_CONTROL:
            router_summary = build_turn_category_summary(state)
            return (
                "System / Meta Control.\n"
                f"Pack: {state.world_pack_id or 'none'}\n"
                f"Stage: {state.scenario_position.current_stage}\n"
                f"Stalled story turns: {router_summary['stalled_story_turns']}\n"
                f"Last routed category: {router_summary['last_resolved_category'] or 'none'}"
            )
        if turn_category.resolved_category == CATEGORY_CREATIVE_EXPANSION:
            return (
                "Creative expansion is non-canonical until chosen.\n"
                f"Current live choices remain: {', '.join(current_choices) if current_choices else 'type a new action'}."
            )
        if turn_category.resolved_category == CATEGORY_TERMINATION_EXIT:
            return (
                "Termination / Exit.\n"
                "Type 'quit' to end the launcher session, or choose a final in-story move if you want the scene to close inside canon."
            )
        return "Turn routed through utility control."

    def _resolve_pipeline_request(
        self,
        request: StoryRequest,
    ) -> tuple[StoryRequest, bool, dict[str, Any] | None]:
        metadata = dict(request.metadata)
        normalized_input = request.player_input.strip()
        if not normalized_input:
            return request, False, None

        lowered_input = normalized_input.lower()
        for prefix in PIPELINE_COMMAND_PREFIXES:
            if lowered_input == prefix or lowered_input.startswith(f"{prefix} "):
                spec = self._parse_inline_pipeline_command(normalized_input[len(prefix):].strip(), prefix)
                metadata["pipeline_command"] = prefix
                return (
                    StoryRequest(
                        player_id=request.player_id,
                        player_input=request.player_input,
                        session_id=request.session_id,
                        choice_id=request.choice_id,
                        metadata=metadata,
                    ),
                    True,
                    spec,
                )
        for prefix in PIPELINE_FILE_COMMAND_PREFIXES:
            if lowered_input == prefix or lowered_input.startswith(f"{prefix} "):
                spec = self._parse_file_pipeline_command(normalized_input[len(prefix):].strip(), prefix)
                metadata["pipeline_command"] = prefix
                return (
                    StoryRequest(
                        player_id=request.player_id,
                        player_input=request.player_input,
                        session_id=request.session_id,
                        choice_id=request.choice_id,
                        metadata=metadata,
                    ),
                    True,
                    spec,
                )
        return request, False, None

    def _parse_inline_pipeline_command(self, body: str, prefix: str) -> dict[str, Any]:
        usage = self._pipeline_usage_text()
        if "::" not in body:
            return {
                "ok": False,
                "reason": "missing_separator",
                "message": f"{prefix} requires '::' between header and source text.",
                "usage": usage,
                "mode": "text",
            }
        header, _, raw_text = body.partition("::")
        header = header.strip()
        raw_text = raw_text.strip()
        if not raw_text:
            return {
                "ok": False,
                "reason": "missing_source_text",
                "message": "Pipeline source text is required.",
                "usage": usage,
                "mode": "text",
            }
        try:
            parts = shlex.split(header)
        except ValueError as exc:
            return {
                "ok": False,
                "reason": "invalid_header",
                "message": f"Could not parse pipeline header: {exc}",
                "usage": usage,
                "mode": "text",
            }
        if len(parts) < 2:
            return {
                "ok": False,
                "reason": "missing_target_or_title",
                "message": "Pipeline command requires both a target and a title.",
                "usage": usage,
                "mode": "text",
            }
        return {
            "ok": True,
            "mode": "text",
            "target": parts[0],
            "title": " ".join(parts[1:]).strip(),
            "raw_text": raw_text,
        }

    def _parse_file_pipeline_command(self, body: str, prefix: str) -> dict[str, Any]:
        usage = self._pipeline_usage_text()
        try:
            parts = shlex.split(body)
        except ValueError as exc:
            return {
                "ok": False,
                "reason": "invalid_header",
                "message": f"Could not parse pipeline file command: {exc}",
                "usage": usage,
                "mode": "file",
            }
        if len(parts) < 3:
            return {
                "ok": False,
                "reason": "missing_target_title_or_path",
                "message": "Pipeline file command requires a target, title, and file path.",
                "usage": usage,
                "mode": "file",
            }
        target = parts[0]
        title = " ".join(parts[1:-1]).strip()
        source_path = parts[-1]
        if not title:
            return {
                "ok": False,
                "reason": "missing_title",
                "message": "Pipeline file command requires a non-empty title.",
                "usage": usage,
                "mode": "file",
            }
        return {
            "ok": True,
            "mode": "file",
            "target": target,
            "title": title,
            "source_path": source_path,
        }

    def _process_pipeline_request(
        self,
        state: StoryState,
        request: StoryRequest,
        pipeline_spec: dict[str, Any] | None,
    ) -> OutputPackage:
        if not pipeline_spec or not pipeline_spec.get("ok", False):
            issue = pipeline_spec or {
                "reason": "missing_pipeline_spec",
                "message": "Pipeline command could not be resolved.",
                "usage": self._pipeline_usage_text(),
            }
            return self._build_pipeline_boundary_output(state, issue)

        raw_text = ""
        source_path = None
        if pipeline_spec["mode"] == "file":
            source_path = self._resolve_pipeline_source_path(str(pipeline_spec["source_path"]))
            if not source_path.exists():
                return self._build_pipeline_boundary_output(
                    state,
                    {
                        "reason": "missing_source_file",
                        "message": f"Pipeline source file was not found: {source_path}",
                        "usage": self._pipeline_usage_text(),
                    },
                )
            try:
                raw_text = self._load_pipeline_source_text(source_path)
            except ValueError as exc:
                return self._build_pipeline_boundary_output(
                    state,
                    {
                        "reason": "unreadable_source_file",
                        "message": str(exc),
                        "usage": self._pipeline_usage_text(),
                    },
                )
        else:
            raw_text = str(pipeline_spec.get("raw_text", "")).strip()

        pipeline_request = PipelineRequest(
            raw_text=raw_text,
            title=str(pipeline_spec["title"]),
            target=str(pipeline_spec["target"]),
        )
        orchestrator_state = self.pipeline_orchestrator.run(pipeline_request)
        translation_lane_status = self._pipeline_translation_status()
        backend_import_payload = None
        if orchestrator_state.engine_handoff is not None:
            backend_import_payload = self._commit_pipeline_backend_import(
                state,
                pipeline_request=pipeline_request,
                source_mode=pipeline_spec["mode"],
                source_path=str(source_path) if source_path is not None else "",
                handoff=orchestrator_state.engine_handoff,
            )
        state.runtime_lanes[PIPELINE_STATE_ID] = {
            "request": {
                "target": pipeline_request.target,
                "title": pipeline_request.title,
                "source_mode": pipeline_spec["mode"],
                "source_path": str(source_path) if source_path is not None else "",
                "raw_text_length": len(pipeline_request.raw_text),
            },
            "orchestrator_state": asdict(orchestrator_state),
            "backend_import_id": (
                str(backend_import_payload.get("import_id", ""))
                if isinstance(backend_import_payload, dict)
                else ""
            ),
            "llm": dict(translation_lane_status),
            "updatedAt": utc_now(),
        }
        self._record_pipeline_llm_history(state, request, translation_lane_status)
        state.updated_at = utc_now()

        scene = Scene(
            text=self._pipeline_scene_text(
                orchestrator_state,
                pipeline_request,
                source_path,
                backend_import_committed=backend_import_payload is not None,
                backend_build_payload=(
                    backend_import_payload.get("backend_build")
                    if isinstance(backend_import_payload, dict)
                    else None
                ),
            ),
            characters=["Pipeline Orchestrator"],
            choices=[
                '/pipeline game "Demo Title" :: source text goes here',
                '/pipeline movie "Demo Title" :: source text goes here',
                '/ingest-file game "Demo Title" "C:\\path\\to\\source.md"',
            ],
            tone="steady",
            consequence_tags=["utility:pipeline", f"pipeline:{'ok' if orchestrator_state.pipeline_ok else 'halted'}"],
        )
        package = package_output(
            state=state,
            scene=scene,
            world_update={},
            memory_update=[],
            canon_update=[],
            image_prompt=None,
            ending=None,
            reasoning_trace=self._pipeline_reasoning_trace(orchestrator_state, pipeline_request),
        )
        package.state_summary["pipeline"] = {
            "requested": True,
            "ok": orchestrator_state.pipeline_ok,
            "current_stage": orchestrator_state.current_stage,
            "last_completed_stage": orchestrator_state.last_completed_stage,
            "support_resume_from_last_valid_stage": orchestrator_state.support_resume_from_last_valid_stage,
            "error": orchestrator_state.error.to_payload() if orchestrator_state.error is not None else None,
            "engine_handoff_ready": orchestrator_state.engine_handoff is not None,
            "backend_import_committed": backend_import_payload is not None,
            "backend_build_committed": bool(
                isinstance(backend_import_payload, dict)
                and isinstance(backend_import_payload.get("backend_build"), dict)
            ),
            "source_mode": pipeline_spec["mode"],
            "source_path": str(source_path) if source_path is not None else "",
        }
        if backend_import_payload is not None:
            package.state_summary["backend_import"] = {
                "imported": True,
                "import_id": backend_import_payload["import_id"],
                "target": backend_import_payload["target"],
                "scene_count": backend_import_payload["scene_count"],
                "runtime_lane": BACKEND_IMPORT_STATE_ID,
            }
            if isinstance(backend_import_payload.get("backend_build"), dict):
                package.state_summary["backend_build"] = dict(backend_import_payload["backend_build"])
        package.state_summary["runtime_lane"] = PIPELINE_STATE_ID
        package.state_summary["llm"] = translation_lane_status
        package.state_summary["llm_history_entries"] = len(state.llm_history)
        package.state_summary["lumen"] = {
            "mode": "skipped",
            "persona": "LUMEN",
            "cartridge": getattr(state, "world_pack_id", None) or "none",
            "version": self.lumen_renderer.version,
            "style_source": "skipped:pipeline",
            "rendered_visual_recall": False,
            "rendered_hooks": 0,
            "request_text": request.player_input,
        }
        if self.aris_runtime is not None:
            package.state_summary["aris_runtime"] = self.aris_runtime.summary(state)
        self._save_session(state)
        self._autosave_if_configured(state)
        return package

    def _commit_pipeline_backend_import(
        self,
        state: StoryState,
        *,
        pipeline_request: PipelineRequest,
        source_mode: str,
        source_path: str,
        handoff: Any,
    ) -> dict[str, Any]:
        artifact = build_backend_import_artifact(
            session_id=state.session_id,
            handoff=handoff,
            source_mode=source_mode,
            source_path=source_path,
        )
        backend_build = self.backend_build_pipeline.run_from_handoff(
            session_id=state.session_id,
            handoff=handoff,
            source_mode=source_mode,
            source_path=source_path,
            source_title=pipeline_request.title,
        )
        prior_lane = self._lane_entry(state, BACKEND_IMPORT_STATE_ID)
        history = list(prior_lane.get("history", [])) if isinstance(prior_lane.get("history", []), list) else []
        history.append(
            {
                "import_id": artifact.import_id,
                "title": artifact.title,
                "target": artifact.target,
                "scene_count": artifact.scene_count,
                "imported_at": artifact.imported_at,
            }
        )
        history = history[-12:]
        payload = artifact.to_payload()
        backend_build_payload = backend_build.to_payload()
        state.runtime_lanes[BACKEND_IMPORT_STATE_ID] = {
            "active_import": payload,
            "history": history,
            "source_pipeline": {
                "title": pipeline_request.title,
                "target": pipeline_request.target,
                "source_mode": source_mode,
                "source_path": source_path,
            },
            "backend_build_id": backend_build.build_id,
            "updatedAt": utc_now(),
        }
        backend_prior_lane = self._lane_entry(state, BACKEND_BUILD_STATE_ID)
        backend_history = (
            list(backend_prior_lane.get("history", []))
            if isinstance(backend_prior_lane.get("history", []), list)
            else []
        )
        backend_history.append(
            {
                "build_id": backend_build.build_id,
                "scene_id": backend_build.export_package.scene_id,
                "scene_count": backend_build_payload["scene_count"],
                "output_dir": backend_build.output_dir,
            }
        )
        state.runtime_lanes[BACKEND_BUILD_STATE_ID] = {
            "active_build": backend_build_payload,
            "history": backend_history[-12:],
            "updatedAt": utc_now(),
        }
        payload["backend_build"] = backend_build_payload
        return payload

    def _build_pipeline_boundary_output(
        self,
        state: StoryState,
        issue: dict[str, Any],
    ) -> OutputPackage:
        scene = Scene(
            text=f"{issue['message']}\n\n{issue.get('usage', self._pipeline_usage_text())}",
            characters=["Pipeline Orchestrator"],
            choices=[
                '/pipeline game "Demo Title" :: source text goes here',
                '/pipeline movie "Demo Title" :: source text goes here',
                '/ingest-file game "Demo Title" "C:\\path\\to\\source.md"',
            ],
            tone="steady",
            consequence_tags=["utility:pipeline", "pipeline:rejected"],
        )
        package = package_output(
            state=state,
            scene=scene,
            world_update={},
            memory_update=[],
            canon_update=[],
            image_prompt=None,
            ending=None,
            reasoning_trace=[f"pipeline request rejected at boundary: {issue['reason']}"],
        )
        package.state_summary["pipeline"] = {
            "requested": True,
            "ok": False,
            "reason": issue["reason"],
            "message": issue["message"],
            "engine_handoff_ready": False,
        }
        package.state_summary["runtime_lane"] = PIPELINE_STATE_ID
        package.state_summary["llm"] = {
            "requested": False,
            "configured": False,
            "mode": "stability",
            "provider": "skipped:pipeline_boundary",
            "approved": False,
            "degraded": False,
        }
        package.state_summary["llm_history_entries"] = len(state.llm_history)
        package.state_summary["lumen"] = {
            "mode": "skipped",
            "persona": "LUMEN",
            "cartridge": getattr(state, "world_pack_id", None) or "none",
            "version": self.lumen_renderer.version,
            "style_source": "skipped:pipeline_boundary",
            "rendered_visual_recall": False,
            "rendered_hooks": 0,
        }
        if self.aris_runtime is not None:
            package.state_summary["aris_runtime"] = self.aris_runtime.summary(state)
        return package

    def _pipeline_scene_text(
        self,
        orchestrator_state: Any,
        pipeline_request: PipelineRequest,
        source_path: Path | None,
        *,
        backend_import_committed: bool,
        backend_build_payload: dict[str, Any] | None,
    ) -> str:
        lines = [
            "Pipeline contract run complete." if orchestrator_state.pipeline_ok else "Pipeline halted.",
            f"Target: {pipeline_request.target}",
            f"Title: {pipeline_request.title}",
        ]
        if source_path is not None:
            lines.append(f"Source File: {source_path}")
        lines.append(f"Current stage: {orchestrator_state.current_stage}")
        lines.append(f"Last completed stage: {orchestrator_state.last_completed_stage or 'none'}")
        lines.append(
            "Engine handoff: ready"
            if orchestrator_state.engine_handoff is not None
            else "Engine handoff: blocked"
        )
        lines.append(
            "Backend import: committed"
            if backend_import_committed
            else "Backend import: not committed"
        )
        if backend_build_payload is not None:
            lines.append("Backend build: packaged")
            lines.append(f"Backend scene count: {backend_build_payload.get('scene_count', 0)}")
            lines.append(
                "Continuity: passed"
                if backend_build_payload.get("continuity_passed", False)
                else "Continuity: warnings locked"
            )
        else:
            lines.append("Backend build: not available")
        if orchestrator_state.error is not None:
            lines.append("")
            lines.append(f"Error: {orchestrator_state.error.error_type}")
            lines.append(orchestrator_state.error.message)
        return "\n".join(lines)

    def _pipeline_reasoning_trace(
        self,
        orchestrator_state: Any,
        pipeline_request: PipelineRequest,
    ) -> list[str]:
        trace = [
            f"pipeline target: {pipeline_request.target}",
            f"pipeline title: {pipeline_request.title}",
        ]
        trace.extend(
            f"{entry.stage}: {'ok' if entry.ok else 'failed'} ({entry.detail})"
            for entry in orchestrator_state.execution_log
        )
        if orchestrator_state.error is not None:
            trace.append(
                f"pipeline halted with {orchestrator_state.error.error_type}: {orchestrator_state.error.message}"
            )
        return trace

    def _pipeline_translation_status(self) -> dict[str, object]:
        translation_lane = getattr(self.pipeline_orchestrator, "translation_lane", None)
        status = getattr(translation_lane, "last_status", None)
        if isinstance(status, dict):
            return dict(status)
        return {
            "requested": self.llm_runtime is not None and self.llm_runtime.requested,
            "configured": (
                self.llm_runtime is not None
                and self.llm_runtime.translation_provider is not None
            ),
            "mode": "translation_only",
            "provider": "none",
            "approved": False,
            "degraded": False,
            "used": False,
            "audit": [],
        }

    def _record_pipeline_llm_history(
        self,
        state: StoryState,
        request: StoryRequest,
        llm_status: dict[str, object],
    ) -> None:
        if not llm_status.get("requested") and not llm_status.get("configured"):
            return
        state.llm_history.append(
            {
                "entry_id": make_id("llm"),
                "timestamp": utc_now(),
                "request_text": request.player_input,
                "mode": str(llm_status.get("mode", "translation_only")),
                "provider": str(llm_status.get("provider", "none")),
                "approved": bool(llm_status.get("approved", False)),
                "degraded": bool(llm_status.get("degraded", False)),
                "text": "",
                "audit": list(llm_status.get("audit", [])),
            }
        )
        if self.llm_runtime is not None and len(state.llm_history) > self.llm_runtime.history_limit:
            del state.llm_history[:-self.llm_runtime.history_limit]

    def _pipeline_usage_text(self) -> str:
        return (
            "Pipeline commands:\n"
            '  /pipeline <target> "<title>" :: <raw source text>\n'
            '  /ingest-file <target> "<title>" "<path-to-.txt|.md|.docx|.csv>"\n'
            "Valid targets: movie, game"
        )

    def _coerce_pipeline_source_path(self, source_path_text: str) -> Path:
        path = Path(source_path_text).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        return path

    def _repair_utf8_mojibake_text(self, text: str) -> str | None:
        if not any(marker in text for marker in ("â", "Ã", "€", "™", "œ", "ž", "�")):
            return None
        for encoding in ("cp1252", "latin-1"):
            try:
                repaired = text.encode(encoding).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            if repaired != text:
                return repaired
        return None

    def _resolve_pipeline_source_path(self, source_path_text: str) -> Path:
        candidate_texts: list[str] = []
        seen_texts: set[str] = set()

        def add_candidate(text: str | None) -> None:
            if not text or text in seen_texts:
                return
            seen_texts.add(text)
            candidate_texts.append(text)

        add_candidate(source_path_text)
        add_candidate(unicodedata.normalize("NFC", source_path_text))
        add_candidate(unicodedata.normalize("NFKC", source_path_text))
        repaired = self._repair_utf8_mojibake_text(source_path_text)
        if repaired is not None:
            add_candidate(repaired)
            add_candidate(unicodedata.normalize("NFC", repaired))
            add_candidate(unicodedata.normalize("NFKC", repaired))

        fallback_path: Path | None = None
        for candidate_text in candidate_texts:
            candidate_path = self._coerce_pipeline_source_path(candidate_text)
            if fallback_path is None:
                fallback_path = candidate_path
            if candidate_path.exists():
                return candidate_path
        return fallback_path or self._coerce_pipeline_source_path(source_path_text)

    def _load_pipeline_source_text(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".docx":
            try:
                with ZipFile(path) as archive:
                    xml = archive.read("word/document.xml").decode("utf-8")
            except Exception as exc:  # pragma: no cover - defensive file boundary
                raise ValueError(f"Could not read DOCX source file: {path}") from exc
            # Preserve Word paragraph boundaries so downstream scene chunking can
            # treat DOCX manuscripts like paragraph-based prose instead of one
            # monolithic block.
            text = re.sub(r"</w:p>", "\n\n", xml)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"[ \t]+\n", "\n", text)
            text = re.sub(r"\n[ \t]+", "\n", text)
            text = re.sub(r"[ \t]+", " ", text)
            text = unescape(text).strip()
            if not text:
                raise ValueError(f"DOCX source file did not contain readable text: {path}")
            return text

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise ValueError(f"Could not read source file: {path}") from exc
        text = text.strip()
        if not text:
            raise ValueError(f"Source file was empty: {path}")
        return text

    def _resolve_movie_request(
        self,
        request: StoryRequest,
    ) -> tuple[StoryRequest, bool, str | None]:
        metadata = dict(request.metadata)
        normalized_input = request.player_input.strip()
        if not normalized_input:
            return request, False, None

        lowered_input = normalized_input.lower()
        for prefix in MOVIE_RENDER_COMMAND_PREFIXES:
            if lowered_input == prefix or lowered_input.startswith(f"{prefix} "):
                body = normalized_input[len(prefix):].strip()
                title, presentation_mode, parse_error = self._parse_movie_command_body(body)
                metadata["movie_command"] = prefix
                metadata["movie_presentation_mode"] = presentation_mode
                if parse_error is not None:
                    metadata["movie_request_error"] = parse_error
                if metadata == request.metadata:
                    return request, True, title
                return (
                    StoryRequest(
                        player_id=request.player_id,
                        player_input=request.player_input,
                        session_id=request.session_id,
                        choice_id=request.choice_id,
                        metadata=metadata,
                    ),
                    True,
                    title,
                )
        return request, False, None

    def _parse_movie_command_body(
        self,
        body: str,
    ) -> tuple[str | None, str, str | None]:
        if not body.strip():
            return None, "backend", None

        try:
            tokens = shlex.split(body)
        except ValueError as exc:
            return None, "backend", f"Could not parse movie command: {exc}"

        title_tokens: list[str] = []
        presentation_mode = "backend"
        index = 0
        while index < len(tokens):
            token = tokens[index]
            lowered = token.lower()
            if lowered == "--lumen":
                presentation_mode = "lumen"
            elif lowered in {"--backend", "--no-lumen"}:
                presentation_mode = "backend"
            elif lowered.startswith("--presentation="):
                presentation_mode = lowered.split("=", 1)[1].strip() or "backend"
            elif lowered.startswith("presentation_mode=") or lowered.startswith("presentation-mode="):
                presentation_mode = lowered.split("=", 1)[1].strip() or "backend"
            elif lowered == "--presentation":
                index += 1
                if index >= len(tokens):
                    return None, "backend", "Movie presentation flag requires a mode."
                presentation_mode = str(tokens[index]).strip().lower() or "backend"
            elif lowered in {"presentation_mode", "presentation-mode"}:
                index += 1
                if index >= len(tokens):
                    return None, "backend", "Movie presentation mode requires a value."
                presentation_mode = str(tokens[index]).strip().lower() or "backend"
            else:
                title_tokens.append(token)
            index += 1

        if presentation_mode not in {"backend", "lumen"}:
            return (
                None,
                "backend",
                f"Unsupported movie presentation mode '{presentation_mode}'. Use 'backend' or 'lumen'.",
            )

        title = " ".join(title_tokens).strip() or None
        if title is not None and title.lower() in _MOVIE_RENDER_DEFAULT_TITLE_TOKENS:
            title = None
        return title, presentation_mode, None

    def _resolve_lane_request(
        self,
        state: StoryState,
        request: StoryRequest,
    ) -> tuple[StoryRequest, str | None]:
        metadata = dict(request.metadata)
        normalized_input = request.player_input.strip()
        requested_lane_raw = str(metadata.get("lane", "")).strip().lower()
        requested_lane = (
            TEXT_TO_3D_WORLD_LANE_ID
            if requested_lane_raw in TEXT_TO_3D_WORLD_LANE_ALIASES
            else None
        )

        if requested_lane is None and normalized_input:
            lowered_input = normalized_input.lower()
            for prefix in TEXT_TO_3D_WORLD_COMMAND_PREFIXES:
                if lowered_input == prefix or lowered_input.startswith(f"{prefix} "):
                    requested_lane = TEXT_TO_3D_WORLD_LANE_ID
                    normalized_input = normalized_input[len(prefix):].strip()
                    metadata["lane_command"] = prefix
                    break

        if requested_lane is None:
            return request, None

        if not normalized_input:
            normalized_input = self._default_text_to_3d_prompt(state)
            metadata["lane_autofill"] = True

        metadata["lane"] = requested_lane
        if normalized_input == request.player_input and metadata == request.metadata:
            return request, requested_lane

        return (
            StoryRequest(
                player_id=request.player_id,
                player_input=normalized_input,
                session_id=request.session_id,
                choice_id=request.choice_id,
                metadata=metadata,
            ),
            requested_lane,
        )

    def _default_text_to_3d_prompt(self, state: StoryState) -> str:
        lane_entry = self._lane_entry(state, TEXT_TO_3D_WORLD_LANE_ID)
        prior_state = lane_entry.get("priorState", {})
        if isinstance(prior_state, dict):
            next_text = str(prior_state.get("nextText", "") or "").strip()
            if next_text:
                return next_text

        last_output = lane_entry.get("lastOutput", {})
        if isinstance(last_output, dict):
            next_text = str(last_output.get("nextText", "") or "").strip()
            if next_text:
                return next_text
        return "Continue the scene."

    def _process_movie_render_request(
        self,
        state: StoryState,
        request: StoryRequest,
        title: str | None,
    ) -> OutputPackage:
        from story_forge.movie_renderer import CompletionGateError

        movie_request_error = str(request.metadata.get("movie_request_error", "") or "").strip()
        if movie_request_error:
            scene = Scene(
                text=(
                    f"{movie_request_error}\n\n"
                    "Use '/movie' for backend-only export or '/movie presentation_mode=lumen' "
                    "for optional presentation shaping."
                ),
                characters=["Movie Renderer"],
                choices=["/movie", "/movie presentation_mode=lumen"],
                tone="steady",
                consequence_tags=["utility:movie_render", "status:invalid_request"],
            )
            package = package_output(
                state=state,
                scene=scene,
                world_update={},
                memory_update=[],
                canon_update=[],
                image_prompt=None,
                ending=None,
                reasoning_trace=["movie render blocked: invalid movie command"],
            )
            package.state_summary["movie_render"] = {
                "rendered": False,
                "reason": movie_request_error,
                "presentation_mode": str(request.metadata.get("movie_presentation_mode", "backend")),
            }
            package.state_summary["runtime_lane"] = MOVIE_RENDER_STATE_ID
            package.state_summary["llm"] = {
                "requested": self.llm_runtime is not None and self.llm_runtime.requested,
                "configured": (
                    self.llm_runtime is not None
                    and self.llm_runtime.translation_provider is not None
                ),
                "mode": "translation_only",
                "provider": "skipped:movie_render",
                "approved": False,
                "degraded": False,
            }
            package.state_summary["llm_history_entries"] = len(state.llm_history)
            package.state_summary["lumen"] = {
                "mode": "skipped",
                "persona": "LUMEN",
                "cartridge": getattr(state, "world_pack_id", None) or "none",
                "version": self.lumen_renderer.version,
                "style_source": "skipped:movie_render",
                "rendered_visual_recall": False,
                "rendered_hooks": 0,
                "request_text": request.player_input,
            }
            if self.aris_runtime is not None:
                package.state_summary["aris_runtime"] = self.aris_runtime.summary(state)
            state.last_scene = scene
            state.updated_at = utc_now()
            self._save_session(state)
            self._autosave_if_configured(state)
            return package

        presentation_mode = str(request.metadata.get("movie_presentation_mode", "backend") or "backend")
        committed_state = None
        try:
            result = self.render_movie(
                state.session_id,
                title=title,
                presentation_mode=presentation_mode,
            )
            committed_state = deepcopy(self._require_session(state.session_id))
        except CompletionGateError as exc:
            scene = Scene(
                text=(
                    f"{exc}\n\n"
                    "Movie export was blocked by the completion audit. "
                    "Fix the audit findings and try '/movie' again."
                ),
                characters=["Movie Renderer"],
                choices=["/3d continue the scene", "/movie"],
                tone="steady",
                consequence_tags=["utility:movie_render", "status:audit_blocked"],
            )
            package = package_output(
                state=state,
                scene=scene,
                world_update={},
                memory_update=[],
                canon_update=[],
                image_prompt=None,
                ending=None,
                reasoning_trace=["movie render blocked by completion audit"],
            )
            package.state_summary["movie_render"] = {
                "rendered": False,
                "completion_audit_passed": False,
                "reason": str(exc),
                "presentation_mode": presentation_mode,
            }
            package.state_summary["runtime_lane"] = MOVIE_RENDER_STATE_ID
        except ValueError as exc:
            scene = Scene(
                text=(
                    f"{exc}\n\n"
                    "Use '/3d <scene prompt>' first, then choose '/movie' to export the run."
                ),
                characters=["Movie Renderer"],
                choices=["/3d A moonlit threshold waits beyond the gate."],
                tone="steady",
                consequence_tags=["utility:movie_render", "status:unavailable"],
            )
            package = package_output(
                state=state,
                scene=scene,
                world_update={},
                memory_update=[],
                canon_update=[],
                image_prompt=None,
                ending=None,
                reasoning_trace=["movie render blocked: no /3d lane history"],
            )
            package.state_summary["movie_render"] = {
                "rendered": False,
                "reason": str(exc),
                "presentation_mode": presentation_mode,
            }
            package.state_summary["runtime_lane"] = MOVIE_RENDER_STATE_ID
        else:
            scene = Scene(
                text=(
                    "Movie export ready.\n"
                    f"Title: {result.title}\n"
                    f"Scenes: {result.scene_count}\n"
                    f"Video: {result.video_path}\n"
                    f"Screenplay: {result.screenplay_path}\n"
                    f"Shot List: {result.shot_list_path}\n"
                    f"Metadata: {result.metadata_path}\n"
                    f"Audit: {result.audit_path}\n"
                    f"Output Folder: {result.output_dir}"
                ),
                characters=["Movie Renderer"],
                choices=["/3d continue the scene", "/movie"],
                tone="steady",
                consequence_tags=["utility:movie_render", "status:rendered"],
            )
            package = package_output(
                state=state,
                scene=scene,
                world_update={},
                memory_update=[],
                canon_update=[],
                image_prompt=None,
                ending=None,
                reasoning_trace=[
                    "movie export assembled from bounded /3d lane history",
                    f"movie title: {result.title}",
                    f"movie scenes: {result.scene_count}",
                ],
            )
            package.state_summary["movie_render"] = {
                "rendered": True,
                "title": result.title,
                "render_id": result.render_id,
                "scene_count": result.scene_count,
                "output_dir": str(result.output_dir),
                "video_path": str(result.video_path),
                "frames_dir": str(result.frames_dir),
                "screenplay_path": str(result.screenplay_path),
                "shot_list_path": str(result.shot_list_path),
                "metadata_path": str(result.metadata_path),
                "audit_path": str(result.audit_path or ""),
                "audit_witness": result.audit_witness,
                "completion_audit_passed": True,
                "source_lane": TEXT_TO_3D_WORLD_LANE_ID,
                "presentation_mode": result.presentation_mode,
                "narration_source": result.narration_source,
            }
            package.state_summary["runtime_lane"] = MOVIE_RENDER_STATE_ID
            if committed_state is not None:
                state = committed_state

        package.state_summary["llm"] = {
            "requested": self.llm_runtime is not None and self.llm_runtime.requested,
            "configured": (
                self.llm_runtime is not None
                and self.llm_runtime.translation_provider is not None
            ),
            "mode": "translation_only",
            "provider": "skipped:movie_render",
            "approved": False,
            "degraded": False,
        }
        package.state_summary["llm_history_entries"] = len(state.llm_history)
        if package.state_summary["movie_render"].get("presentation_mode") == "lumen":
            package.state_summary["lumen"] = {
                "mode": "cinematic_presentation_only",
                "persona": "LUMEN",
                "cartridge": getattr(state, "world_pack_id", None) or "none",
                "version": self.lumen_renderer.version,
                "style_source": "movie_render",
                "rendered_visual_recall": False,
                "rendered_hooks": 0,
                "request_text": request.player_input,
            }
        else:
            package.state_summary["lumen"] = {
                "mode": "skipped",
                "persona": "LUMEN",
                "cartridge": getattr(state, "world_pack_id", None) or "none",
                "version": self.lumen_renderer.version,
                "style_source": "skipped:movie_render",
                "rendered_visual_recall": False,
                "rendered_hooks": 0,
                "request_text": request.player_input,
            }
        if self.aris_runtime is not None:
            package.state_summary["aris_runtime"] = self.aris_runtime.summary(state)
        state.last_scene = scene
        state.updated_at = utc_now()
        self._save_session(state)
        self._autosave_if_configured(state)
        return package

    def _scheduled_event_to_forced_event(self, scheduled_event: Any) -> Event:
        payload = dict(scheduled_event.payload)
        outcome = str(
            payload.get("outcome")
            or f"A scheduled {scheduled_event.event_type} pressure arrives from the story timeline."
        )
        location_id = payload.get("location_id") if isinstance(payload.get("location_id"), str) else None
        next_location_id = (
            payload.get("next_location_id")
            if isinstance(payload.get("next_location_id"), str)
            else None
        )
        return Event(
            event_id=scheduled_event.scheduled_id,
            event_type=scheduled_event.event_type,
            participants=["player"],
            outcome=outcome,
            impact_level=int(payload.get("impact_level", 2)),
            tags=["scheduled", scheduled_event.event_type],
            location_id=location_id,
            next_location_id=next_location_id,
        )

    def _schedule_expiry_followups(self, state: StoryState, expired_event_ids: list[str]) -> None:
        if not expired_event_ids:
            return
        expired_lookup = {
            event.event_id: event
            for event in state.active_events
            if event.event_id in expired_event_ids
        }
        for event_id in expired_event_ids:
            expired_event = expired_lookup.get(event_id)
            if expired_event is None:
                continue
            follow_up_type = expired_event.payload.get("expiry_schedule_event_type")
            if not isinstance(follow_up_type, str) or not follow_up_type:
                continue
            try:
                delay_turns = max(0, int(expired_event.payload.get("expiry_schedule_delay_turns", 0)))
            except (TypeError, ValueError):
                delay_turns = 0
            schedule_event(
                state=state,
                event_type=follow_up_type,
                trigger_turn=state.turn_count + delay_turns,
                source_event_id=expired_event.event_id,
                source="active_event_expiry",
                payload={"expired_from": expired_event.event_type},
            )

    def _require_session(self, session_id: str) -> StoryState:
        state = self.get_session(session_id)
        if state is None:
            raise ValueError(f"Session '{session_id}' was not found.")
        return state
