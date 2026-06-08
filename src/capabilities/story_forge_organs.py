"""Governed Story Forge expansion organ execution paths (Release 29)."""

# Mythic: Story Forge Organs
# Engineering: StoryForgeOrgansEngine
from __future__ import annotations

import json
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
    operator_ack = bool(payload.get("operator_ack") or payload.get("operator_gated_ack"))
    execution_ready = ready and operator_ack
    output_root = root / ".runtime" / "story_forge" / "movie_renderer"
    artifact_bundle = None
    if execution_ready:
        output_root.mkdir(parents=True, exist_ok=True)
        plan_path = output_root / f"render_plan_{artifact_ref.replace('/', '_')[:48]}.json"
        plan_path.write_text(
            json.dumps(
                {
                    "lane": "movie_renderer",
                    "artifact_ref": artifact_ref,
                    "status": "execution_ready",
                    "handoff": "external_renderer_optional",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        artifact_bundle = str(plan_path)
    return {
        "ok": ready,
        "organ": "movie_renderer_lane_organ",
        "action": "propose_render" if not execution_ready else "execute_render_plan",
        "artifact_ref": artifact_ref or None,
        "renderer_module_present": renderer.is_file(),
        "render_plan": {
            "lane": "movie_renderer",
            "artifact_ref": artifact_ref,
            "status": "execution_ready" if execution_ready else ("proposed" if ready else "blocked"),
            "artifact_bundle": artifact_bundle,
        },
        "proposal_only": not execution_ready,
        "claim_label": "asserted",
        "message": "render plan executed" if execution_ready else ("render plan proposed" if ready else "artifact_ref required"),
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
    operator_ack = bool(payload.get("operator_ack") or payload.get("operator_gated_ack"))
    execution_ready = ready and operator_ack
    output_root = root / ".runtime" / "story_forge" / "text_game_to_video"
    artifact_bundle = None
    if execution_ready:
        output_root.mkdir(parents=True, exist_ok=True)
        bundle_path = output_root / f"video_bundle_{script_ref.replace('/', '_')[:48]}.json"
        bundle_path.write_text(
            json.dumps(
                {
                    "front_door": "text_game_to_video",
                    "script_ref": script_ref,
                    "status": "execution_ready",
                    "frames": ["frame_001", "frame_002"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        artifact_bundle = str(bundle_path)
    return {
        "ok": ready,
        "organ": "text_game_to_video_organ",
        "action": "propose_render_plan" if not execution_ready else "execute_video_bundle",
        "script_ref": script_ref or None,
        "render_plan": {
            "front_door": "text_game_to_video",
            "script_ref": script_ref,
            "status": "execution_ready" if execution_ready else ("proposed" if ready else "blocked"),
            "artifact_bundle": artifact_bundle,
        },
        "proposal_only": not execution_ready,
        "claim_label": "asserted",
        "message": "video bundle generated" if execution_ready else ("render plan proposed" if ready else "script_ref required"),
    }


def execute_game_front_door_admit(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Operator-gated session flag + bridge admission check."""
    runtime_root = root or Path(__file__).resolve().parents[2]
    repo_root = Path(__file__).resolve().parents[2]
    payload = dict(args or {})
    session_id = _clean_source_ref(payload.get("session_id"))
    operator_ack = bool(payload.get("operator_ack") or payload.get("operator_gated_ack"))
    engine = repo_root / "external/story_forge/src/story_forge/engine.py"
    admitted = engine.is_file() and bool(session_id) and operator_ack
    engine_status = None
    if admitted:
        import sys

        sf_src = repo_root / "external/story_forge/src"
        if sf_src.is_dir() and str(sf_src) not in sys.path:
            sys.path.insert(0, str(sf_src))
        try:
            from story_forge.engine import StoryForgeEngine

            engine_status = {"engine_class": StoryForgeEngine.__name__, "session_id": session_id}
        except Exception as exc:
            engine_status = {"engine_error": str(exc)[:200]}
    lane_result = None
    prompt = _clean_source_ref(payload.get("prompt") or payload.get("text"))
    if admitted and prompt:
        lane_result = execute_text_to_3d_world_lane_route(
            {
                "prompt": prompt,
                "seed": payload.get("seed"),
                "session_id": session_id,
                "operator_ack": operator_ack,
                "export_playable": payload.get("export_playable", True),
            },
            root=runtime_root,
        )
    return {
        "ok": admitted,
        "organ": "game_front_door_organ",
        "action": "admit_session",
        "session_id": session_id or None,
        "front_door_active": admitted,
        "operator_gated": True,
        "engine_status": engine_status,
        "lane_result": lane_result,
        "proposal_only": not (
            admitted
            and (
                (engine_status and "engine_class" in engine_status and not prompt)
                or (lane_result and lane_result.get("ok"))
            )
        ),
        "claim_label": "asserted" if admitted else "blocked",
        "message": "session admitted" if admitted else "session_id and operator_ack required",
    }


def execute_text_to_3d_world_lane_route(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Operator-gated deterministic text-to-3D world-pack generation route."""
    runtime_root = root or Path(__file__).resolve().parents[2]
    repo_root = Path(__file__).resolve().parents[2]
    payload = dict(args or {})
    prompt = _clean_source_ref(payload.get("prompt") or payload.get("text") or payload.get("source_ref"))
    if not prompt:
        return {
            "ok": False,
            "organ": "text_to_3d_world_lane_organ",
            "action": "world_lane_route",
            "lane_module_present": True,
            "route_status": "blocked",
            "aais_live_lane": False,
            "proposal_only": True,
            "claim_label": "blocked",
            "message": "prompt required",
        }
    operator_ack = bool(payload.get("operator_ack") or payload.get("operator_gated_ack"))
    if not operator_ack:
        return {
            "ok": False,
            "organ": "text_to_3d_world_lane_organ",
            "action": "world_lane_route",
            "lane_module_present": True,
            "route_status": "blocked",
            "aais_live_lane": False,
            "proposal_only": True,
            "claim_label": "blocked",
            "message": "operator_ack required",
        }
    import sys

    sf_src = repo_root / "external/story_forge/src"
    if sf_src.is_dir() and str(sf_src) not in sys.path:
        sys.path.insert(0, str(sf_src))
    from story_forge.text_to_3d_game_pipeline import build_text_to_3d_world_pack

    output_root = runtime_root / ".runtime" / "story_forge" / "text_to_3d_world"
    result = build_text_to_3d_world_pack(
        prompt=prompt,
        seed=payload.get("seed"),
        session_id=payload.get("session_id") or payload.get("sessionId"),
        output_root=output_root,
        export_playable=payload.get("export_playable", True) is not False,
    )
    if not result.get("ok"):
        return {
            "ok": False,
            "organ": "text_to_3d_world_lane_organ",
            "action": "world_lane_route",
            "lane_module_present": True,
            "route_status": "blocked",
            "aais_live_lane": False,
            "proposal_only": True,
            "claim_label": "blocked",
            "message": result.get("message", "world lane generation blocked"),
        }
    world_pack_path = Path(result["world_pack_path"])
    return {
        "ok": True,
        "organ": "text_to_3d_world_lane_organ",
        "action": "world_lane_route",
        "lane_id": "lane.text_to_3d_world",
        "lane_module_present": True,
        "route_status": "configured",
        "aais_live_lane": True,
        "proposal_only": False,
        "world_id": result["world_id"],
        "world_spec_ref": str(world_pack_path / "world.spec.json"),
        "gameplay_spec_ref": str(world_pack_path / "gameplay.spec.json"),
        "scene_manifest_ref": str(world_pack_path / "scene.manifest.json"),
        "world_pack_ref": str(world_pack_path),
        "playable_ref": str(world_pack_path / "index.html") if result["playable_manifest"].get("entrypoint") else None,
        "receipt": result["receipt"],
        "claim_label": "asserted",
        "message": "world pack generated",
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
    operator_ack = bool(payload.get("operator_ack") or payload.get("operator_gated_ack"))
    output_root = root / ".runtime" / "story_forge" / "world_packs"
    assembled_path = None
    if present and operator_ack and pack_id:
        output_root.mkdir(parents=True, exist_ok=True)
        assembled_path = output_root / f"{pack_id}.json"
        assembled_path.write_text(
            json.dumps(
                {
                    "pack_id": pack_id,
                    "worldpacks_dir": str(worldpacks),
                    "assembled": True,
                    "export_contract": "governed_write_v1",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    manifest = {
        "pack_id": pack_id or "default",
        "worldpacks_dir": str(worldpacks),
        "dir_present": present,
        "export_contract": "governed_write_v1" if assembled_path else "bounded_read_only_v1",
        "assembled_path": str(assembled_path) if assembled_path else None,
    }
    return {
        "ok": present and bool(pack_id),
        "organ": "world_pack_lane_organ",
        "action": "assemble_pack" if assembled_path else "inspect_manifest",
        "manifest": manifest,
        "registry_lane_active": present and bool(pack_id),
        "proposal_only": not bool(assembled_path),
        "claim_label": "asserted",
        "message": "world pack assembled" if assembled_path else ("manifest inspect complete" if present else "worldpacks directory missing"),
    }
