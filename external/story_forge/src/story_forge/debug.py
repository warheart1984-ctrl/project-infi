from __future__ import annotations

from typing import Any

from story_forge.models import StoryState
from story_forge.persistence import to_primitive


def state_view(state: StoryState) -> dict[str, object]:
    return {
        "session_id": state.session_id,
        "player_id": state.player_id,
        "world_pack_id": state.world_pack_id,
        "runtime_mode": state.runtime_mode,
        "turn_count": state.turn_count,
        "progress": state.progress,
        "canon_mode": state.canon_mode.value,
        "current_location_id": state.player_state.current_location_id,
        "current_arc": state.scenario_position.current_arc,
        "current_stage": state.scenario_position.current_stage,
        "stage_turn_count": state.scenario_position.stage_turn_count,
        "arc_flags": dict(state.scenario_position.arc_flags),
        "timeline_marker": state.world_state.timeline_marker,
        "environment_flags": list(state.world_state.environment_flags),
        "active_events": len([event for event in state.active_events if not event.resolved]),
        "scheduled_events": len([event for event in state.scheduled_events if not event.fired]),
        "location_history_entries": len(state.location_history),
        "ending_scores": dict(state.ending_scores),
        "character_ids": sorted(state.characters.keys()),
        "runtime_lane_ids": sorted(state.runtime_lanes.keys()),
        "visual_artifact_ids": list(state.visual_memory.artifact_ids),
        "visual_pending_recall": state.visual_memory.pending_context is not None,
        "visual_hook_state": dict(state.visual_memory.hook_state),
        "runtime_status": build_runtime_status(state),
    }


def build_runtime_status(
    state: StoryState,
    report: Any | None = None,
) -> dict[str, object]:
    integrity = state.aris_runtime.integrity
    errors = list(getattr(report, "errors", integrity.get("last_errors", [])) or [])
    warnings = list(getattr(report, "warnings", integrity.get("last_warnings", [])) or [])
    due_unfired = [
        event
        for event in state.scheduled_events
        if not event.fired and event.trigger_turn < state.turn_count
    ]
    return {
        "runtime_mode": state.runtime_mode,
        "integrity_profile": integrity.get("profile_mode", state.runtime_mode),
        "base_path": integrity.get("base_path", ""),
        "bundle_path": integrity.get("bundle_path", ""),
        "frozen": bool(integrity.get("frozen", False)),
        "required_files": list(integrity.get("required_paths", [])),
        "required_file_count": len(integrity.get("required_paths", [])),
        "missing_required_files": list(integrity.get("missing", [])),
        "missing_required_file_count": len(integrity.get("missing", [])),
        "scenario_arc": state.scenario_position.current_arc,
        "scenario_stage": state.scenario_position.current_stage,
        "stage_turn_count": state.scenario_position.stage_turn_count,
        "scheduled_events_total": len(state.scheduled_events),
        "scheduled_events_due_unfired": len(due_unfired),
        "active_events_total": len(state.active_events),
        "active_events_unresolved": len([event for event in state.active_events if not event.resolved]),
        "failing_invariants": errors,
        "soft_observations": warnings,
        "last_integrity_errors": errors,
        "last_integrity_warnings": warnings,
    }


def memory_view(state: StoryState) -> list[dict[str, object]]:
    return [to_primitive(entry) for entry in state.memory_board]


def canon_view(state: StoryState) -> list[dict[str, object]]:
    return [to_primitive(entry) for entry in state.canon_ledger if not entry.retracted]


def recent_event_view(state: StoryState) -> list[dict[str, object]]:
    return [to_primitive(event) for event in state.recent_events]


def active_event_view(state: StoryState) -> list[dict[str, object]]:
    return [to_primitive(event) for event in state.active_events]


def scheduled_event_view(state: StoryState) -> list[dict[str, object]]:
    return [to_primitive(event) for event in state.scheduled_events]


def location_history_view(state: StoryState) -> list[dict[str, object]]:
    return [to_primitive(entry) for entry in state.location_history]


def event_trace_view(state: StoryState) -> list[str]:
    return list(state.event_trace)


def decision_trace_view(state: StoryState) -> list[str]:
    return list(state.decision_trace)
