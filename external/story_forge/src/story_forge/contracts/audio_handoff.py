from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from typing import TYPE_CHECKING, Any

from story_forge.backend_full_build import BackendBuildArtifact


if TYPE_CHECKING:
    from story_forge.movie_renderer import MovieRenderResult


def _as_dicts(items: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            rows.append(deepcopy(item))
        elif is_dataclass(item):
            rows.append(asdict(item))
        else:
            rows.append(dict(vars(item)))
    return rows


@dataclass(slots=True)
class AudioPipelineHandoff:
    source_artifact_type: str
    session_id: str
    build_id: str
    story_id: str
    run_id: str
    scene_id: str
    title: str
    target: str
    tone: str
    screenplay: str
    video_path: str | None
    shots: list[dict[str, Any]] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    dialogue_lines: list[dict[str, Any]] = field(default_factory=list)
    narration_lines: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    continuity_passed: bool = False
    continuity_issues: list[str] = field(default_factory=list)
    output_dir: str = ""
    screenplay_path: str = ""
    shot_list_path: str = ""
    metadata_path: str = ""
    audit_path: str = ""
    audit_digest: str = ""
    audit_witness: str = ""

    def with_video_path(self, video_path: str | None) -> "AudioPipelineHandoff":
        return replace(self, video_path=video_path)

    def to_payload(self) -> dict[str, Any]:
        return {
            "source_artifact_type": self.source_artifact_type,
            "session_id": self.session_id,
            "build_id": self.build_id,
            "story_id": self.story_id,
            "run_id": self.run_id,
            "scene_id": self.scene_id,
            "title": self.title,
            "target": self.target,
            "tone": self.tone,
            "screenplay": self.screenplay,
            "video_path": self.video_path,
            "shots": deepcopy(self.shots),
            "entities": deepcopy(self.entities),
            "dialogue_lines": deepcopy(self.dialogue_lines),
            "narration_lines": deepcopy(self.narration_lines),
            "metadata": deepcopy(self.metadata),
            "continuity_passed": self.continuity_passed,
            "continuity_issues": list(self.continuity_issues),
            "output_dir": self.output_dir,
            "screenplay_path": self.screenplay_path,
            "shot_list_path": self.shot_list_path,
            "metadata_path": self.metadata_path,
            "audit_path": self.audit_path,
            "audit_digest": self.audit_digest,
            "audit_witness": self.audit_witness,
        }


def build_audio_pipeline_handoff(
    artifact: BackendBuildArtifact,
    *,
    story_id: str | None = None,
    run_id: str | None = None,
    video_path: str | None = None,
    narration_lines: list[dict[str, Any]] | None = None,
) -> AudioPipelineHandoff:
    try:
        from story_forge.backend_import import BackendImportArtifact
    except Exception:  # noqa: BLE001
        BackendImportArtifact = None  # type: ignore[assignment]

    if BackendImportArtifact is not None and isinstance(artifact, BackendImportArtifact):
        raise TypeError(
            "Audio pipeline handoff requires BackendBuildArtifact; "
            "BackendImportArtifact is not rich enough for Story Forge audio."
        )
    if not isinstance(artifact, BackendBuildArtifact):
        raise TypeError(
            "Audio pipeline handoff requires BackendBuildArtifact from story_forge.backend_full_build."
        )

    scene_id = artifact.export_package.scene_id
    if artifact.scene_object.scene_id != scene_id:
        raise ValueError("Scene object scene_id does not match export package scene_id.")
    if artifact.temporal_shot_list.scene_id != scene_id:
        raise ValueError("Temporal shot list scene_id does not match export package scene_id.")
    if artifact.final_sequence.scene_id != scene_id:
        raise ValueError("Final sequence scene_id does not match export package scene_id.")

    metadata = deepcopy(artifact.export_package.metadata)
    resolved_story_id = str(story_id or metadata.get("story_id") or scene_id)
    resolved_run_id = str(run_id or metadata.get("run_id") or artifact.build_id)
    resolved_video_path = video_path if video_path is not None else artifact.export_package.video_path
    resolved_dialogue_lines = deepcopy(metadata.get("dialogue_lines", []))
    resolved_narration_lines = deepcopy(
        narration_lines if narration_lines is not None else metadata.get("narration_lines", [])
    )

    return AudioPipelineHandoff(
        source_artifact_type="backend_full_build",
        session_id=artifact.session_id,
        build_id=artifact.build_id,
        story_id=resolved_story_id,
        run_id=resolved_run_id,
        scene_id=scene_id,
        title=str(metadata.get("source_title") or scene_id),
        target=str(metadata.get("target") or "movie"),
        tone=str(metadata.get("tone") or artifact.narrative_state.tone),
        screenplay=artifact.export_package.screenplay,
        video_path=str(resolved_video_path) if resolved_video_path else None,
        shots=_as_dicts(list(artifact.temporal_shot_list.shots)),
        entities=_as_dicts(list(artifact.scene_object.entities)),
        dialogue_lines=resolved_dialogue_lines,
        narration_lines=resolved_narration_lines,
        metadata=metadata,
        continuity_passed=artifact.continuity_report.passed,
        continuity_issues=list(artifact.continuity_report.issues),
        output_dir=artifact.output_dir,
        screenplay_path=artifact.screenplay_path,
        shot_list_path=artifact.shot_list_path,
        metadata_path=artifact.metadata_path,
        audit_path=artifact.audit_path,
        audit_digest=str(metadata.get("audit_digest") or ""),
        audit_witness=artifact.audit_witness,
    )


def attach_movie_render_result(
    handoff: AudioPipelineHandoff,
    result: "MovieRenderResult",
) -> AudioPipelineHandoff:
    metadata = deepcopy(handoff.metadata)
    metadata.update(
        {
            "movie_render_id": result.render_id,
            "movie_presentation_mode": result.presentation_mode,
            "movie_narration_source": result.narration_source,
            "movie_output_dir": str(result.output_dir),
            "movie_frames_dir": str(result.frames_dir),
            "movie_audit_path": str(result.audit_path) if result.audit_path else "",
        }
    )
    return replace(
        handoff,
        video_path=str(result.video_path),
        metadata=metadata,
    )
