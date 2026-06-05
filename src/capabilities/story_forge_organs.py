"""Governed Story Forge expansion organ execution paths (Release 29)."""

# Engineering: StoryForgeOrgansEngine
from __future__ import annotations

from pathlib import Path
from typing import Any


def _clean_source_ref(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()[:512]


def execute_story_forge_launcher_intake(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Structured source handoff; admits front door when preconditions pass."""
    root = root or Path(__file__).resolve().parents[2]
    payload = dict(args or {})
    source_ref = _clean_source_ref(
        payload.get("source_ref") or payload.get("structured_source") or payload.get("source")
    )
    launcher = root / "external/story_forge/src/story_forge/launcher.py"
    admitted = launcher.is_file() and bool(source_ref)
    return {
        "ok": admitted,
        "organ": "story_forge_launcher_organ",
        "action": "intake",
        "source_ref": source_ref or None,
        "launcher_module_present": launcher.is_file(),
        "front_door_active": admitted,
        "proposal_only": not admitted,
        "claim_label": "asserted" if admitted else "blocked",
        "message": "intake admitted" if admitted else "source_ref and launcher module required",
    }


def execute_movie_renderer_lane_render(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Propose movie render step post-BackendBuildArtifact (no repo writes)."""
    root = root or Path(__file__).resolve().parents[2]
    payload = dict(args or {})
    artifact_ref = _clean_source_ref(
        payload.get("backend_build_artifact_ref") or payload.get("artifact_ref")
    )
    renderer = root / "external/story_forge/src/story_forge/movie_renderer.py"
    ready = renderer.is_file() and bool(artifact_ref)
    return {
        "ok": ready,
        "organ": "movie_renderer_lane_organ",
        "action": "propose_render",
        "artifact_ref": artifact_ref or None,
        "renderer_module_present": renderer.is_file(),
        "render_plan": {
            "lane": "movie_renderer",
            "artifact_ref": artifact_ref,
            "status": "proposed" if ready else "blocked",
        },
        "proposal_only": True,
        "claim_label": "asserted",
        "message": "render plan proposed" if ready else "artifact_ref required",
    }


def execute_text_game_to_video_plan(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Governed propose-render-plan (proposal-only)."""
    root = root or Path(__file__).resolve().parents[2]
    payload = dict(args or {})
    script_ref = _clean_source_ref(payload.get("script_ref") or payload.get("narrative_ref"))
    engine = root / "external/story_forge/src/story_forge/engine.py"
    ready = engine.is_file() and bool(script_ref)
    return {
        "ok": ready,
        "organ": "text_game_to_video_organ",
        "action": "propose_render_plan",
        "script_ref": script_ref or None,
        "render_plan": {
            "front_door": "text_game_to_video",
            "script_ref": script_ref,
            "status": "proposed" if ready else "blocked",
        },
        "proposal_only": True,
        "claim_label": "asserted",
        "message": "render plan proposed" if ready else "script_ref required",
    }


def execute_game_front_door_admit(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Operator-gated session flag + bridge admission check."""
    root = root or Path(__file__).resolve().parents[2]
    payload = dict(args or {})
    session_id = _clean_source_ref(payload.get("session_id"))
    operator_ack = bool(payload.get("operator_ack") or payload.get("operator_gated_ack"))
    engine = root / "external/story_forge/src/story_forge/engine.py"
    admitted = engine.is_file() and bool(session_id) and operator_ack
    return {
        "ok": admitted,
        "organ": "game_front_door_organ",
        "action": "admit_session",
        "session_id": session_id or None,
        "front_door_active": admitted,
        "operator_gated": True,
        "proposal_only": not admitted,
        "claim_label": "asserted" if admitted else "blocked",
        "message": "session admitted" if admitted else "session_id and operator_ack required",
    }


def execute_text_to_3d_world_lane_route(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Read-only world-lane posture; returns not_configured until lane is live."""
    root = root or Path(__file__).resolve().parents[2]
    lane = root / "external/story_forge/src/story_forge/text_to_3d_world_lane.py"
    configured = bool((args or {}).get("force_configured")) and lane.is_file()
    return {
        "ok": True,
        "organ": "text_to_3d_world_lane_organ",
        "action": "world_lane_route",
        "lane_module_present": lane.is_file(),
        "route_status": "configured" if configured else "not_configured",
        "aais_live_lane": configured,
        "proposal_only": True,
        "claim_label": "asserted",
        "message": "world lane route stub (not_configured)" if not configured else "world lane stub route",
    }


def execute_world_pack_lane_inspect(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Pack manifest inspect + bounded export contract (read-only)."""
    root = root or Path(__file__).resolve().parents[2]
    payload = dict(args or {})
    pack_id = _clean_source_ref(payload.get("pack_id") or payload.get("world_pack_id"))
    worldpacks = root / "external/story_forge/src/story_forge/worldpacks"
    present = worldpacks.is_dir()
    manifest = {
        "pack_id": pack_id or "default",
        "worldpacks_dir": str(worldpacks),
        "dir_present": present,
        "export_contract": "bounded_read_only_v1",
    }
    return {
        "ok": present,
        "organ": "world_pack_lane_organ",
        "action": "inspect_manifest",
        "manifest": manifest,
        "registry_lane_active": present and bool(pack_id),
        "proposal_only": True,
        "claim_label": "asserted",
        "message": "manifest inspect complete" if present else "worldpacks directory missing",
    }
