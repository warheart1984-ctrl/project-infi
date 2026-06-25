"""Governed Story Forge -> BeatBox -> Speakers capability wrapper."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import os
import sys
from typing import Any

from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseViolationError,
    assert_executable,
    get_component,
    is_executable,
    register_component,
)


CAPABILITY_NAME = "story_forge_audio"
CAPABILITY_VERSION = "v1"
STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID = "jarvis.capability.story_forge_audio"

StoryForgeAudioCapability = {
    "name": CAPABILITY_NAME,
    "version": CAPABILITY_VERSION,
    "input": "BackendBuildArtifact",
    "output": "FinalMovieArtifact",
    "requires": ["rendered_video_path", "dialogue_lines|narration_lines"],
    "deterministic": True,
    "side_effects": ["audio_render", "video_assembly"],
}


def _clean_text(value: Any, default: str = "") -> str:
    text = " ".join(str(value or "").split()).strip()
    return text or default


def resolve_story_forge_src(story_forge_src: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if story_forge_src is not None:
        candidates.append(Path(story_forge_src))

    env_path = os.environ.get("AAIS_STORY_FORGE_SRC", "").strip()
    if env_path:
        candidates.append(Path(env_path))

    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / "external" / "story_forge" / "src")
    candidates.append(repo_root.parent / "story forge" / "src")

    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if (resolved / "story_forge").exists():
            return resolved

    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        "Could not locate Story Forge src directory for AAIS story_forge_audio capability. "
        f"Searched: {searched}"
    )


def ensure_story_forge_src(story_forge_src: str | Path | None = None) -> Path:
    resolved = resolve_story_forge_src(story_forge_src)
    resolved_str = str(resolved)
    if resolved_str not in sys.path:
        sys.path.insert(0, resolved_str)
    return resolved


def ensure_story_forge_audio_capability_registered() -> None:
    try:
        get_component(STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID)
        return
    except ComponentNotRegisteredError:
        pass

    register_component(
        GovernedComponent(
            component_id=STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID,
            name="Story Forge Audio Capability",
            component_type="capability",
            phase=Phase.VALIDATED,
            allowed_contexts=["operator_runtime", "test_harness"],
            notes=(
                "Governed Story Forge movie/audio pipeline. "
                "Validated for operator and test harness contexts only."
            ),
            validation_metadata=deepcopy(StoryForgeAudioCapability),
        )
    )


def authority_allows(runtime_context: str = "operator_runtime") -> bool:
    ensure_story_forge_audio_capability_registered()
    return is_executable(STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID, runtime_context)


def _story_forge_types(story_forge_src: str | Path | None = None) -> tuple[type[Any], Any]:
    ensure_story_forge_src(story_forge_src)
    from story_forge.backend_full_build import BackendBuildArtifact
    from story_forge.movie_audio_pipeline import run_story_forge_movie_audio_pipeline

    return BackendBuildArtifact, run_story_forge_movie_audio_pipeline


def _artifact_identity(artifact: Any) -> dict[str, str]:
    scene_id = ""
    if hasattr(artifact, "export_package"):
        scene_id = _clean_text(getattr(artifact.export_package, "scene_id", ""))
    return {
        "session_id": _clean_text(getattr(artifact, "session_id", "")),
        "story_id": _clean_text(getattr(getattr(artifact, "export_package", None), "metadata", {}).get("story_id", scene_id)),
        "run_id": _clean_text(getattr(artifact, "build_id", "")),
        "scene_id": scene_id,
    }


def _artifact_from_request(request: dict[str, Any] | None) -> Any:
    if not isinstance(request, dict):
        return None
    return request.get("artifact") or request.get("backend_build_artifact")


def _base_output(
    *,
    status: str,
    request_identity: dict[str, str] | None = None,
    rendered_video_path: str = "",
    final_audio_path: str = "",
    movie_path: str = "",
    voice_stem_path: str = "",
    music_stem_path: str = "",
    mix_version: str = "",
    continuity_passed: bool = False,
    issue_count: int = 0,
    error_type: str | None = None,
    message: str = "",
) -> dict[str, Any]:
    identity = dict(request_identity or {})
    return {
        "status": status,
        "capability": deepcopy(StoryForgeAudioCapability),
        "artifact_type": "FinalMovieArtifact",
        "session_id": identity.get("session_id", ""),
        "story_id": identity.get("story_id", ""),
        "run_id": identity.get("run_id", ""),
        "scene_id": identity.get("scene_id", ""),
        "rendered_video_path": rendered_video_path,
        "final_audio_path": final_audio_path,
        "movie_path": movie_path,
        "voice_stem_path": voice_stem_path,
        "music_stem_path": music_stem_path,
        "mix_version": mix_version,
        "continuity_passed": bool(continuity_passed),
        "issue_count": int(issue_count),
        "deterministic": True,
        "error_type": error_type,
        "message": _clean_text(message),
    }


def _with_ul_substrate(result: dict[str, Any]) -> dict[str, Any]:
    from src.aais_ul.runtime import wrap_runtime_snapshot

    return wrap_runtime_snapshot(result)


def validate_request(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("Request must be a dict.")

    story_forge_src = request.get("story_forge_src")
    BackendBuildArtifact, _ = _story_forge_types(story_forge_src)

    artifact = request.get("artifact") or request.get("backend_build_artifact")
    if artifact is None:
        raise ValueError("artifact is required.")
    if not isinstance(artifact, BackendBuildArtifact):
        raise ValueError("artifact must be a BackendBuildArtifact.")

    rendered_video_value = _clean_text(
        request.get("rendered_video_path") or request.get("video_path")
    )
    if not rendered_video_value:
        raise ValueError("rendered_video_path is required.")
    rendered_video_path = Path(rendered_video_value)
    if not rendered_video_path.exists():
        raise FileNotFoundError(f"rendered_video_path does not exist: {rendered_video_path}")

    metadata = dict(getattr(artifact.export_package, "metadata", {}) or {})
    if not metadata.get("dialogue_lines") and not metadata.get("narration_lines"):
        raise ValueError(
            "Story Forge audio capability requires dialogue_lines or narration_lines in the artifact metadata."
        )

    output_root = _clean_text(request.get("output_root"))
    if not output_root:
        output_root = str(Path(artifact.output_dir) / "aais_story_forge_audio")

    movie_output_path = _clean_text(request.get("movie_output_path"))
    runtime_context = _clean_text(request.get("runtime_context"), "operator_runtime")

    return {
        "artifact": artifact,
        "rendered_video_path": str(rendered_video_path),
        "output_root": output_root,
        "movie_output_path": movie_output_path,
        "runtime_context": runtime_context,
        "story_forge_src": str(ensure_story_forge_src(story_forge_src)),
        "request_identity": _artifact_identity(artifact),
    }


def enforce_output_contract(result: Any) -> dict[str, Any]:
    pipeline_result = result.result
    mix_plan = pipeline_result.mix_plan
    voice_stem_path = ""
    music_stem_path = ""
    mix_version = ""
    continuity_passed = False
    issue_count = 0
    if mix_plan is not None:
        voice_stem_path = _clean_text(getattr(getattr(mix_plan, "voice_stem", None), "file_path", ""))
        music_stem_path = _clean_text(getattr(getattr(mix_plan, "music_stem", None), "file_path", ""))
        mix_version = _clean_text(getattr(mix_plan, "mix_version", ""))
        continuity_passed = bool(getattr(mix_plan, "continuity_passed", False))
        issue_count = len(list(getattr(mix_plan, "issues", []) or []))

    contract = _base_output(
        status="completed" if pipeline_result.ok else "failed",
        request_identity={
            "session_id": _clean_text(getattr(pipeline_result, "session_id", "")),
            "story_id": _clean_text(getattr(pipeline_result, "story_id", "")),
            "run_id": _clean_text(getattr(pipeline_result, "run_id", "")),
            "scene_id": _clean_text(getattr(pipeline_result, "scene_id", "")),
        },
        rendered_video_path=_clean_text(getattr(result.handoff, "video_path", "")),
        final_audio_path=_clean_text(getattr(pipeline_result, "final_audio_path", "")),
        movie_path=_clean_text(getattr(pipeline_result, "movie_path", "")),
        voice_stem_path=voice_stem_path,
        music_stem_path=music_stem_path,
        mix_version=mix_version,
        continuity_passed=continuity_passed,
        issue_count=issue_count,
        error_type=_clean_text(getattr(pipeline_result, "error_type", "")) or None,
        message=_clean_text(getattr(pipeline_result, "message", "")),
    )

    if contract["status"] == "completed":
        required_fields = ("session_id", "story_id", "run_id", "scene_id", "final_audio_path", "movie_path")
        missing = [field for field in required_fields if not contract.get(field)]
        if missing:
            raise ValueError(f"Completed Story Forge audio capability result is missing fields: {missing}")
    else:
        if not contract["error_type"]:
            raise ValueError("Failed Story Forge audio capability result is missing error_type.")

    return contract


def run_story_forge_audio_capability(request: dict[str, Any]) -> dict[str, Any]:
    runtime_context = _clean_text(
        request.get("runtime_context") if isinstance(request, dict) else "",
        "operator_runtime",
    )

    ensure_story_forge_audio_capability_registered()
    try:
        assert_executable(STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID, runtime_context)
    except PhaseViolationError as exc:
        artifact = _artifact_from_request(request if isinstance(request, dict) else None)
        return _with_ul_substrate(
            _base_output(
                status="rejected",
                request_identity=_artifact_identity(artifact) if artifact is not None else None,
                rendered_video_path=_clean_text(
                    request.get("rendered_video_path") or request.get("video_path")
                ) if isinstance(request, dict) else "",
                error_type="AuthorityRejected",
                message=str(exc),
            )
        )

    try:
        validated = validate_request(request)
    except Exception as exc:  # noqa: BLE001
        artifact = _artifact_from_request(request if isinstance(request, dict) else None)
        return _with_ul_substrate(
            _base_output(
                status="rejected",
                request_identity=_artifact_identity(artifact) if artifact is not None else None,
                rendered_video_path=_clean_text(
                    request.get("rendered_video_path") or request.get("video_path")
                ) if isinstance(request, dict) else "",
                error_type="ValidationRejected",
                message=str(exc),
            )
        )

    _, run_story_forge_movie_audio_pipeline = _story_forge_types(validated["story_forge_src"])
    result = run_story_forge_movie_audio_pipeline(
        validated["artifact"],
        video_path=validated["rendered_video_path"],
        output_root=validated["output_root"],
        movie_output_path=validated["movie_output_path"],
    )
    return _with_ul_substrate(enforce_output_contract(result))


__all__ = [
    "STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID",
    "StoryForgeAudioCapability",
    "authority_allows",
    "ensure_story_forge_audio_capability_registered",
    "ensure_story_forge_src",
    "enforce_output_contract",
    "run_story_forge_audio_capability",
    "validate_request",
]
