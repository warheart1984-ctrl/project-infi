from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from importlib import import_module
import json
from pathlib import Path
import re
import secrets
import shutil
import tempfile
from typing import Any

from story_forge.contracts.pipeline import LUMEN_MODE_CINEMATIC, TARGET_MOVIE
from story_forge.lumen_renderer import LumenRenderer
from story_forge.models import OutputPackage, Scene, StoryRequest, StoryState
from story_forge.app_paths import default_movie_output_root
from story_forge.render_staging import (
    default_movie_staging_root,
    prepare_movie_staging_root,
    run_movie_staging_janitor,
    write_movie_staging_metadata,
)
from story_forge.text_to_3d_world_lane import (
    LANE_ID as TEXT_TO_3D_WORLD_LANE_ID,
    TextTo3DHistoryEntry,
    TextTo3DWorldLaneError,
)
from story_forge.visual_artifact_schema import unique_strings, unique_tokens


def _default_movie_root() -> Path:
    return default_movie_output_root()


_SUPPORTED_CAPTURE_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp"}
MOVIE_PRESENTATION_BACKEND = "backend"
MOVIE_PRESENTATION_LUMEN = "lumen"
_SUPPORTED_MOVIE_PRESENTATION_MODES = {
    MOVIE_PRESENTATION_BACKEND,
    MOVIE_PRESENTATION_LUMEN,
}


def _render_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return normalized or "movie_export"


def normalize_movie_presentation_mode(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"", "backend", "none", "off", "plain", "deterministic"}:
        return MOVIE_PRESENTATION_BACKEND
    if normalized in {"lumen", "cinematic_lumen"}:
        return MOVIE_PRESENTATION_LUMEN
    supported = ", ".join(sorted(_SUPPORTED_MOVIE_PRESENTATION_MODES))
    raise ValueError(
        f"Unsupported movie presentation mode '{value}'. Use one of: {supported}."
    )


def _wrap_text(text: str, *, width: int) -> list[str]:
    words = str(text or "").split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _render_targets(
    session_dir: Path,
    safe_title: str,
    render_id: str,
) -> tuple[Path, Path, Path, Path, Path]:
    return (
        session_dir / f"{safe_title}_{render_id}_screenplay.txt",
        session_dir / f"{safe_title}_{render_id}_shot_list.json",
        session_dir / f"{safe_title}_{render_id}_metadata.json",
        session_dir / f"{safe_title}_{render_id}.mp4",
        session_dir / f"{safe_title}_{render_id}_frames",
    )


@dataclass(slots=True)
class MovieScene:
    scene_number: int
    heading: str
    lumen_narration: str
    narration_source: str
    visual_hooks: list[str]
    visual_direction: str | None
    duration_estimate: str
    shot_type: str
    capture_references: list[str] = field(default_factory=list)
    capture_details: list[dict[str, Any]] = field(default_factory=list)
    transition_ids: list[str] = field(default_factory=list)
    scene_graph_handle: str = ""
    tick: int = 0
    narrative_score: int = 0


@dataclass(slots=True)
class MovieRenderResult:
    title: str
    render_id: str
    scene_count: int
    presentation_mode: str
    narration_source: str
    output_dir: Path
    screenplay_path: Path
    shot_list_path: Path
    metadata_path: Path
    video_path: Path
    frames_dir: Path
    audit_path: Path | None = None
    audit_witness: str = ""


@dataclass(slots=True)
class CompletionAuditCheck:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CompletionAuditReport:
    render_id: str
    title: str
    generated_at: str
    hayley_witness: str
    checks: list[CompletionAuditCheck] = field(default_factory=list)
    artifact_path: Path | None = None

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def report(self) -> str:
        if self.passed:
            return (
                f"Movie completion audit passed for '{self.title}' "
                f"({self.render_id})."
            )

        lines = [
            f"Movie completion audit failed for '{self.title}' ({self.render_id}).",
        ]
        for check in self.checks:
            if check.passed:
                continue
            lines.append(f"- {check.name}")
            for detail in check.details:
                lines.append(f"  {detail}")
        return "\n".join(lines)


@dataclass(slots=True, frozen=True)
class MovieRuntimeModules:
    cv2: Any
    np: Any
    image: Any
    image_draw: Any
    image_font: Any


class MovieRenderDependencyError(ValueError):
    pass


class CompletionGateError(RuntimeError):
    pass


def _audit_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hayley_witness() -> str:
    return f"hayley-{secrets.token_hex(4)}"


def _read_json_payload(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _check_required_outputs(result: MovieRenderResult) -> CompletionAuditCheck:
    details: list[str] = []
    passed = True
    required_paths = {
        "output directory": result.output_dir,
        "screenplay": result.screenplay_path,
        "shot list": result.shot_list_path,
        "metadata": result.metadata_path,
        "video": result.video_path,
    }

    for label, path in required_paths.items():
        if not path.exists():
            passed = False
            details.append(f"{label} is missing: {path}")
            continue
        if path.is_file() and path.stat().st_size <= 0:
            passed = False
            details.append(f"{label} is empty: {path}")

    if result.video_path.suffix.lower() != ".mp4":
        passed = False
        details.append(f"video output is not an mp4: {result.video_path}")

    if passed:
        details.append("screenplay, shot list, metadata, and mp4 outputs all exist.")
    return CompletionAuditCheck(name="Core outputs", passed=passed, details=details)


def _check_structured_outputs(result: MovieRenderResult) -> CompletionAuditCheck:
    details: list[str] = []
    passed = True

    try:
        screenplay_text = result.screenplay_path.read_text(encoding="utf-8")
    except OSError:
        passed = False
        details.append("screenplay could not be read.")
    else:
        if result.title.upper() not in screenplay_text:
            passed = False
            details.append("screenplay is missing the render title heading.")

    shot_list = _read_json_payload(result.shot_list_path)
    if shot_list is None:
        passed = False
        details.append("shot list is unreadable JSON.")
    else:
        if int(shot_list.get("total_scenes", -1) or -1) != result.scene_count:
            passed = False
            details.append("shot list scene count does not match the render result.")
        if str(shot_list.get("title", "") or "").strip() != result.title:
            passed = False
            details.append("shot list title does not match the render result.")

    metadata = _read_json_payload(result.metadata_path)
    if metadata is None:
        passed = False
        details.append("metadata is unreadable JSON.")
    else:
        if str(metadata.get("render_id", "") or "").strip() != result.render_id:
            passed = False
            details.append("metadata render_id does not match the render result.")
        if str(metadata.get("video_path", "") or "").strip() != str(result.video_path):
            passed = False
            details.append("metadata video_path does not match the render result.")
        if str(metadata.get("runtime_lane", "") or "").strip() != TEXT_TO_3D_WORLD_LANE_ID:
            passed = False
            details.append("metadata runtime_lane does not point at the /3d lane.")

    if passed:
        details.append("screenplay and structured JSON outputs are internally consistent.")
    return CompletionAuditCheck(name="Structured continuity", passed=passed, details=details)


def _check_frame_bundle(result: MovieRenderResult) -> CompletionAuditCheck:
    details: list[str] = []
    passed = True

    if not result.frames_dir.exists():
        return CompletionAuditCheck(
            name="Frame bundle",
            passed=False,
            details=[f"frames directory is missing: {result.frames_dir}"],
        )

    frame_paths = sorted(result.frames_dir.glob("*.png"))
    expected_frames = result.scene_count + 1
    if len(frame_paths) < expected_frames:
        passed = False
        details.append(
            f"expected at least {expected_frames} storyboard frames, found {len(frame_paths)}."
        )
    for frame_path in frame_paths:
        try:
            frame_size = frame_path.stat().st_size
        except OSError:
            passed = False
            details.append(f"frame could not be read: {frame_path}")
            continue
        if frame_size <= 0:
            passed = False
            details.append(f"frame is empty: {frame_path}")

    if passed:
        details.append("storyboard frame bundle is present and non-empty.")
    return CompletionAuditCheck(name="Frame bundle", passed=passed, details=details)


def run_completion_audit(result: MovieRenderResult) -> CompletionAuditReport:
    audit = CompletionAuditReport(
        render_id=result.render_id,
        title=result.title,
        generated_at=_audit_timestamp(),
        hayley_witness=_hayley_witness(),
    )
    audit.checks.append(_check_required_outputs(result))
    audit.checks.append(_check_structured_outputs(result))
    audit.checks.append(_check_frame_bundle(result))
    return audit


def _render_completion_audit_markdown(
    result: MovieRenderResult,
    audit: CompletionAuditReport,
) -> str:
    lines = [
        "# Movie Completion Audit",
        "",
        f"Audit date: {audit.generated_at}",
        f"Render ID: {result.render_id}",
        f"Title: {result.title}",
        f"Hayley witness: {audit.hayley_witness}",
        f"Passed: {'yes' if audit.passed else 'no'}",
        "",
        "## Checklist",
        "",
    ]
    for check in audit.checks:
        marker = "x" if check.passed else " "
        lines.append(f"- [{marker}] {check.name}")
        for detail in check.details:
            lines.append(f"  {detail}")
        lines.append("")

    lines.extend(
        [
            "## Outputs",
            "",
            f"- Video: {result.video_path}",
            f"- Screenplay: {result.screenplay_path}",
            f"- Shot List: {result.shot_list_path}",
            f"- Metadata: {result.metadata_path}",
            f"- Frames: {result.frames_dir}",
            "",
        ]
    )
    return "\n".join(lines)


def write_audit_artifact(
    result: MovieRenderResult,
    audit: CompletionAuditReport,
) -> Path:
    target = result.output_dir / f"{_slug(result.title)}_{result.render_id}_audit.md"
    target.write_text(
        _render_completion_audit_markdown(result, audit),
        encoding="utf-8",
    )
    audit.artifact_path = target
    return target


class MovieRenderer:
    """Render a bounded movie export from lawful /3d lane history."""

    def __init__(
        self,
        *,
        output_root: str | Path | None = None,
        staging_root: str | Path | None = None,
        lumen_renderer: LumenRenderer | None = None,
    ) -> None:
        self.output_root = Path(output_root) if output_root is not None else _default_movie_root()
        self.staging_root = (
            Path(staging_root)
            if staging_root is not None
            else default_movie_staging_root()
        )
        prepare_movie_staging_root(self.staging_root)
        run_movie_staging_janitor(self.staging_root)
        self._lumen_renderer = lumen_renderer
        self.frame_size = (1280, 720)
        self.fps = 1.0
        self._runtime_modules: MovieRuntimeModules | None = None

    def render_movie(
        self,
        state: StoryState,
        *,
        output_dir: str | Path | None = None,
        title: str | None = None,
        presentation_mode: str | None = None,
    ) -> MovieRenderResult:
        lane_entry = self._lane_entry(state)
        movie_title = title.strip() if isinstance(title, str) and title.strip() else self._default_title(state)
        resolved_presentation_mode = normalize_movie_presentation_mode(presentation_mode)
        session_root = Path(output_dir) if output_dir is not None else self.output_root / state.session_id

        safe_title = _slug(movie_title)
        (
            render_id,
            final_output_dir,
            final_screenplay_path,
            final_shot_list_path,
            final_metadata_path,
            final_video_path,
            final_frames_dir,
        ) = self._reserve_render_targets(session_root, safe_title)

        prepare_movie_staging_root(self.staging_root)
        with tempfile.TemporaryDirectory(dir=self.staging_root, prefix="render_") as temp_dir:
            staged_root = Path(temp_dir)
            write_movie_staging_metadata(staged_root, render_id=render_id)
            staged_output_dir = staged_root / final_output_dir.name
            staged_output_dir.mkdir(parents=True, exist_ok=True)
            staged_result = self._run_movie_pipeline(
                state,
                output_dir=staged_output_dir,
                title=movie_title,
                presentation_mode=resolved_presentation_mode,
                lane_entry=lane_entry,
                render_id=render_id,
            )
            audit = run_completion_audit(staged_result)
            if not audit.passed:
                raise CompletionGateError(audit.report)

            admitted_result = self._promote_staged_render(
                staged_result,
                final_output_dir=final_output_dir,
                final_screenplay_path=final_screenplay_path,
                final_shot_list_path=final_shot_list_path,
                final_metadata_path=final_metadata_path,
                final_video_path=final_video_path,
                final_frames_dir=final_frames_dir,
            )

        admitted_result.audit_path = write_audit_artifact(admitted_result, audit)
        admitted_result.audit_witness = audit.hayley_witness
        return admitted_result

    def run_movie_pipeline(
        self,
        state: StoryState,
        *,
        output_dir: str | Path | None = None,
        title: str | None = None,
        presentation_mode: str | None = None,
    ) -> MovieRenderResult:
        return self.render_movie(
            state,
            output_dir=output_dir,
            title=title,
            presentation_mode=presentation_mode,
        )

    def _run_movie_pipeline(
        self,
        state: StoryState,
        *,
        output_dir: str | Path | None = None,
        title: str | None = None,
        presentation_mode: str = MOVIE_PRESENTATION_BACKEND,
        lane_entry: dict[str, Any] | None = None,
        render_id: str | None = None,
    ) -> MovieRenderResult:
        presentation_state = deepcopy(state)
        scenes = self._build_movie_scenes(
            state,
            presentation_state,
            presentation_mode=presentation_mode,
        )
        if not scenes:
            raise ValueError("No /3d lane history is available yet. Play a /3d scene before rendering a movie.")

        movie_title = title.strip() if isinstance(title, str) and title.strip() else self._default_title(state)
        session_dir = Path(output_dir) if output_dir is not None else self.output_root / state.session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        safe_title = _slug(movie_title)
        active_lane_entry = lane_entry if lane_entry is not None else self._lane_entry(state)
        active_render_id = render_id or _render_id()
        screenplay_path, shot_list_path, metadata_path, video_path, frames_dir = _render_targets(
            session_dir,
            safe_title,
            active_render_id,
        )
        frames_dir.mkdir(parents=True, exist_ok=True)

        self._write_screenplay(screenplay_path, movie_title, state, scenes)
        self._write_shot_list(shot_list_path, movie_title, scenes)
        self._render_video(video_path, frames_dir, movie_title, scenes)
        self._write_metadata(
            metadata_path,
            movie_title,
            active_render_id,
            state,
            active_lane_entry,
            scenes,
            video_path,
            frames_dir,
            presentation_mode=presentation_mode,
        )

        narration_source = MOVIE_PRESENTATION_BACKEND
        if scenes and all(scene.narration_source == MOVIE_PRESENTATION_LUMEN for scene in scenes):
            narration_source = MOVIE_PRESENTATION_LUMEN

        return MovieRenderResult(
            title=movie_title,
            render_id=active_render_id,
            scene_count=len(scenes),
            presentation_mode=presentation_mode,
            narration_source=narration_source,
            output_dir=session_dir,
            screenplay_path=screenplay_path,
            shot_list_path=shot_list_path,
            metadata_path=metadata_path,
            video_path=video_path,
            frames_dir=frames_dir,
        )

    def _promote_staged_render(
        self,
        staged_result: MovieRenderResult,
        *,
        final_output_dir: Path,
        final_screenplay_path: Path,
        final_shot_list_path: Path,
        final_metadata_path: Path,
        final_video_path: Path,
        final_frames_dir: Path,
    ) -> MovieRenderResult:
        final_output_dir.parent.mkdir(parents=True, exist_ok=True)
        final_targets = (
            final_screenplay_path,
            final_shot_list_path,
            final_metadata_path,
            final_video_path,
            final_frames_dir,
        )
        if final_output_dir.exists():
            raise CompletionGateError(
                f"Movie completion admission refused because the final package directory already exists: {final_output_dir}"
            )
        if any(path.exists() for path in final_targets):
            existing_path = next(path for path in final_targets if path.exists())
            raise CompletionGateError(
                f"Movie completion admission refused because a final target already exists: {existing_path}"
            )

        try:
            shutil.move(str(staged_result.output_dir), final_output_dir)
        except OSError as exc:
            if final_output_dir.exists():
                shutil.rmtree(final_output_dir, ignore_errors=True)
            raise CompletionGateError(
                f"Movie completion admission failed during final promotion: {exc}"
            ) from exc
        self._rewrite_promoted_metadata(
            final_metadata_path,
            final_video_path=final_video_path,
            final_frames_dir=final_frames_dir,
        )

        return MovieRenderResult(
            title=staged_result.title,
            render_id=staged_result.render_id,
            scene_count=staged_result.scene_count,
            presentation_mode=staged_result.presentation_mode,
            narration_source=staged_result.narration_source,
            output_dir=final_output_dir,
            screenplay_path=final_screenplay_path,
            shot_list_path=final_shot_list_path,
            metadata_path=final_metadata_path,
            video_path=final_video_path,
            frames_dir=final_frames_dir,
        )

    def _rewrite_promoted_metadata(
        self,
        metadata_path: Path,
        *,
        final_video_path: Path,
        final_frames_dir: Path,
    ) -> None:
        payload = _read_json_payload(metadata_path)
        if payload is None:
            raise CompletionGateError(
                f"Movie completion admission could not read promoted metadata: {metadata_path}"
            )
        payload["video_path"] = str(final_video_path)
        payload["frames_dir"] = str(final_frames_dir)
        metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _build_movie_scenes(
        self,
        state: StoryState,
        presentation_state: StoryState,
        *,
        presentation_mode: str,
    ) -> list[MovieScene]:
        scenes: list[MovieScene] = []
        for index, entry in enumerate(self._history_entries(state), start=1):
            output = entry.output
            scene_spec = output.scene_spec
            game_state = output.game_state
            event_records = output.event_records
            capture_details = self._capture_details(event_records)
            visual_hooks = self._approved_visual_hooks(event_records, capture_details)

            location_anchor = scene_spec.get("locationAnchor", {})
            location_label = str(location_anchor.get("label", "Threshold") or "Threshold")
            base_text = str(
                output.next_text
                or scene_spec.get("summary")
                or entry.request_text
                or "The scene reforms around the next transition."
            ).strip()
            shot_type = self._shot_type(index)
            narration, narration_source = self._render_movie_narration(
                state=presentation_state,
                request_text=entry.request_text or "/movie",
                base_text=base_text,
                mood=str(scene_spec.get("mood", "steady") or "steady"),
                focal_labels=self._focal_labels(scene_spec),
                approved_hooks=visual_hooks,
                presentation_mode=presentation_mode,
            )
            scenes.append(
                MovieScene(
                    scene_number=index,
                    heading=self._make_scene_heading(location_label, index, game_state),
                    lumen_narration=narration,
                    narration_source=narration_source,
                    visual_hooks=visual_hooks,
                    visual_direction=self._build_visual_direction(scene_spec, base_text, shot_type),
                    duration_estimate=self._duration_estimate(event_records),
                    shot_type=shot_type,
                    capture_references=self._capture_references(capture_details),
                    capture_details=capture_details,
                    transition_ids=self._transition_ids(event_records),
                    scene_graph_handle=output.scene_graph_handle,
                    tick=int(game_state.get("tick", 0) or 0),
                    narrative_score=int(game_state.get("narrativeScore", 0) or 0),
                )
            )
        return scenes

    def _lane_entry(self, state: StoryState) -> dict[str, Any]:
        lane_entry = state.runtime_lanes.get(TEXT_TO_3D_WORLD_LANE_ID, {})
        return lane_entry if isinstance(lane_entry, dict) else {}

    def _history_entries(self, state: StoryState) -> list[TextTo3DHistoryEntry]:
        lane_entry = self._lane_entry(state)
        history_raw = lane_entry.get("history", [])
        entries: list[TextTo3DHistoryEntry] = []
        if isinstance(history_raw, list):
            for index, entry in enumerate(history_raw, start=1):
                try:
                    entries.append(TextTo3DHistoryEntry.from_payload(entry))
                except TextTo3DWorldLaneError as exc:
                    raise ValueError(
                        f"Text-to-3D history entry {index} is invalid: {exc}"
                    ) from exc
        if entries:
            return entries

        last_output = lane_entry.get("lastOutput", {})
        if isinstance(last_output, dict):
            try:
                return [
                    TextTo3DHistoryEntry(
                        request_text=str(lane_entry.get("lastRequestText", "") or "").strip(),
                        updated_at=str(lane_entry.get("updatedAt", "") or "").strip(),
                        output=TextTo3DHistoryEntry.from_payload(
                            {
                                "requestText": str(lane_entry.get("lastRequestText", "") or "").strip(),
                                "updatedAt": str(lane_entry.get("updatedAt", "") or "").strip(),
                                "output": last_output,
                            }
                        ).output,
                    )
                ]
            except TextTo3DWorldLaneError as exc:
                raise ValueError(
                    f"Text-to-3D lastOutput is invalid: {exc}"
                ) from exc
        return []

    def _default_title(self, state: StoryState) -> str:
        cartridge = (state.world_pack_id or "story_forge").replace("_", " ").title()
        lane_entry = self._lane_entry(state)
        world_id = str(lane_entry.get("worldId", "") or state.session_id[:8]).strip()
        return f"{cartridge} Session {world_id[:12]}"

    def _make_scene_heading(self, location_label: str, index: int, game_state: dict[str, Any]) -> str:
        tick = int(game_state.get("tick", 0) or 0)
        location = location_label.upper().replace("-", " ")
        return f"INT. {location} - SCENE {index:02d} (TICK {tick})"

    def _render_movie_narration(
        self,
        *,
        state: StoryState,
        request_text: str,
        base_text: str,
        mood: str,
        focal_labels: list[str],
        approved_hooks: list[str],
        presentation_mode: str,
    ) -> tuple[str, str]:
        if presentation_mode != MOVIE_PRESENTATION_LUMEN:
            return base_text, MOVIE_PRESENTATION_BACKEND

        package = OutputPackage(
            scene=Scene(
                text=base_text,
                characters=focal_labels[:3] or ["Threshold"],
                choices=[],
                tone=mood,
                consequence_tags=[],
            ),
            world_update={},
            memory_update=[],
            canon_update=[],
            image_prompt=None,
            ending=None,
            ending_flag=False,
            state_summary={
                "lumen_mode": LUMEN_MODE_CINEMATIC,
                "visual_recall": {
                    "triggered": False,
                    "artifact_ids": [],
                    "hooks": [],
                    "context": "",
                },
                "presentation_hooks": list(approved_hooks),
            },
            reasoning_trace=[],
        )
        rendered = self._get_lumen_renderer().render(
            state,
            StoryRequest(
                player_id=state.player_id,
                session_id=state.session_id,
                player_input=request_text,
                metadata={
                    "lumen_mode": LUMEN_MODE_CINEMATIC,
                    "target": TARGET_MOVIE,
                },
            ),
            package,
        )
        if rendered.presentation is not None and rendered.presentation.text.strip():
            return rendered.presentation.text.strip(), MOVIE_PRESENTATION_LUMEN
        return base_text, MOVIE_PRESENTATION_BACKEND

    def _get_lumen_renderer(self) -> LumenRenderer:
        if self._lumen_renderer is None:
            self._lumen_renderer = LumenRenderer()
        return self._lumen_renderer

    def _build_visual_direction(
        self,
        scene_spec: dict[str, Any],
        base_text: str,
        shot_type: str,
    ) -> str:
        location_anchor = scene_spec.get("locationAnchor", {})
        location_label = str(location_anchor.get("label", "Threshold") or "Threshold")
        focal_labels = self._focal_labels(scene_spec)
        focal_segment = ", ".join(focal_labels[:4]) if focal_labels else "architectural silhouettes"
        theme = str(scene_spec.get("theme", "mythic_threshold") or "mythic_threshold").replace("_", " ")
        mood = str(scene_spec.get("mood", "steady") or "steady").replace("_", " ")
        return (
            f"{base_text}. {shot_type.title()} shot in {location_label}. "
            f"Focal objects: {focal_segment}. Theme: {theme}. Mood: {mood}. "
            "Cinematic lighting, filmic composition, continuity preserved."
        )

    def _focal_labels(self, scene_spec: dict[str, Any]) -> list[str]:
        labels: list[str] = []
        focal_objects = scene_spec.get("focalObjects", [])
        if not isinstance(focal_objects, list):
            return labels
        for item in focal_objects:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "") or "").strip()
            if label:
                labels.append(label)
        return labels

    def _duration_estimate(self, event_records: list[dict[str, Any]]) -> str:
        count = max(1, len(event_records))
        if count <= 1:
            return "30 seconds"
        if count == 2:
            return "45 seconds"
        return "60 seconds"

    def _shot_type(self, index: int) -> str:
        shot_types = ("wide", "tracking", "close-up", "overhead")
        return shot_types[(index - 1) % len(shot_types)]

    def _capture_details(self, event_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        details: list[dict[str, Any]] = []
        for event in event_records:
            if not isinstance(event, dict):
                continue
            artifact = str(event.get("observationalCapture", "") or "").strip()
            if not artifact:
                continue
            detail = self._resolve_capture_reference(artifact)
            detail["transition_id"] = str(event.get("transitionId", "") or "").strip()
            detail["event_id"] = str(event.get("eventId", "") or detail.get("event_id", "")).strip()
            detail["event_type"] = str(event.get("type", "") or detail.get("event_type", "")).strip()
            detail["approved_visual_hooks"] = unique_tokens(
                [*detail.get("approved_visual_hooks", []), *self._approved_hooks_from_mapping(event)]
            )
            details.append(detail)
        return details

    def _capture_references(self, capture_details: list[dict[str, Any]]) -> list[str]:
        return unique_strings(
            [
                str(detail.get("reference", "")).strip()
                for detail in capture_details
                if str(detail.get("reference", "")).strip()
            ]
        )

    def _reserve_render_targets(
        self,
        session_root: Path,
        safe_title: str,
    ) -> tuple[str, Path, Path, Path, Path, Path, Path]:
        base_render_id = _render_id()
        candidate_render_id = base_render_id
        suffix = 2
        while True:
            package_dir = session_root / f"{safe_title}_{candidate_render_id}"
            screenplay_path, shot_list_path, metadata_path, video_path, frames_dir = _render_targets(
                package_dir,
                safe_title,
                candidate_render_id,
            )
            if not package_dir.exists():
                return (
                    candidate_render_id,
                    package_dir,
                    screenplay_path,
                    shot_list_path,
                    metadata_path,
                    video_path,
                    frames_dir,
                )
            candidate_render_id = f"{base_render_id}_{suffix:02d}"
            suffix += 1

    def _approved_visual_hooks(
        self,
        event_records: list[dict[str, Any]],
        capture_details: list[dict[str, Any]],
    ) -> list[str]:
        hooks: list[str] = []
        for event in event_records:
            if isinstance(event, dict):
                hooks.extend(self._approved_hooks_from_mapping(event))
        for detail in capture_details:
            hooks.extend(
                str(hook)
                for hook in detail.get("approved_visual_hooks", [])
            )
        return unique_tokens(hooks)

    def _transition_ids(self, event_records: list[dict[str, Any]]) -> list[str]:
        transition_ids: list[str] = []
        for event in event_records:
            if not isinstance(event, dict):
                continue
            transition_id = str(event.get("transitionId", "") or "").strip()
            if transition_id and transition_id not in transition_ids:
                transition_ids.append(transition_id)
        return transition_ids

    def _write_screenplay(
        self,
        path: Path,
        title: str,
        state: StoryState,
        scenes: list[MovieScene],
    ) -> None:
        lines = [
            "=" * 64,
            title.upper(),
            "=" * 64,
            "",
            "Written by Story Forge Movie Renderer",
            f"Session: {state.session_id}",
            f"World Pack: {state.world_pack_id or 'none'}",
            (
                f"Presentation Mode: {scenes[0].narration_source}"
                if scenes
                else f"Presentation Mode: {MOVIE_PRESENTATION_BACKEND}"
            ),
            "",
        ]
        for scene in scenes:
            lines.append(f"{scene.scene_number:03d}. {scene.heading}")
            lines.append("")
            lines.append(scene.lumen_narration)
            lines.append("")
            if scene.visual_hooks:
                lines.append("VISUAL CONTINUITY: " + ", ".join(scene.visual_hooks))
                lines.append("")
            lines.append("-" * 64)
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_shot_list(
        self,
        path: Path,
        title: str,
        scenes: list[MovieScene],
    ) -> None:
        payload = {
            "title": title,
            "total_scenes": len(scenes),
            "generated_by": "Story Forge Movie Renderer",
            "shots": [
                {
                    "scene": scene.scene_number,
                    "heading": scene.heading,
                    "narration": scene.lumen_narration,
                    "narration_source": scene.narration_source,
                    "visual_direction": scene.visual_direction,
                    "shot_type": scene.shot_type,
                    "duration": scene.duration_estimate,
                    "visual_hooks": list(scene.visual_hooks),
                    "capture_references": list(scene.capture_references),
                    "capture_details": list(scene.capture_details),
                    "transition_ids": list(scene.transition_ids),
                    "scene_graph_handle": scene.scene_graph_handle,
                    "tick": scene.tick,
                    "narrative_score": scene.narrative_score,
                }
                for scene in scenes
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_runtime_modules(self) -> MovieRuntimeModules:
        if self._runtime_modules is not None:
            return self._runtime_modules

        missing: list[str] = []
        loaded: dict[str, Any] = {}
        module_targets = {
            "cv2": "opencv-python-headless",
            "numpy": "numpy",
            "PIL.Image": "Pillow",
            "PIL.ImageDraw": "Pillow",
            "PIL.ImageFont": "Pillow",
        }
        for module_name, package_name in module_targets.items():
            try:
                loaded[module_name] = import_module(module_name)
            except ModuleNotFoundError:
                if package_name not in missing:
                    missing.append(package_name)

        if missing:
            missing_display = ", ".join(missing)
            raise MovieRenderDependencyError(
                "Movie rendering dependencies are unavailable. "
                f"Install {missing_display} to use /movie."
            )

        self._runtime_modules = MovieRuntimeModules(
            cv2=loaded["cv2"],
            np=loaded["numpy"],
            image=loaded["PIL.Image"],
            image_draw=loaded["PIL.ImageDraw"],
            image_font=loaded["PIL.ImageFont"],
        )
        return self._runtime_modules

    def _render_video(
        self,
        video_path: Path,
        frames_dir: Path,
        title: str,
        scenes: list[MovieScene],
    ) -> None:
        modules = self._load_runtime_modules()
        frame_paths: list[Path] = []
        title_frame = self._build_title_frame(title, len(scenes))
        title_path = frames_dir / "frame_000.png"
        title_frame.save(title_path)
        frame_paths.append(title_path)

        for index, scene in enumerate(scenes, start=1):
            frame = self._build_scene_frame(scene)
            frame_path = frames_dir / f"frame_{index:03d}.png"
            frame.save(frame_path)
            frame_paths.append(frame_path)

        fourcc = modules.cv2.VideoWriter_fourcc(*"mp4v")
        writer = modules.cv2.VideoWriter(str(video_path), fourcc, self.fps, self.frame_size)
        if not writer.isOpened():
            raise ValueError("Movie renderer could not open a video writer for mp4 export.")
        try:
            for frame_path in frame_paths:
                image = modules.image.open(frame_path).convert("RGB")
                frame = modules.cv2.cvtColor(
                    modules.np.array(image),
                    modules.cv2.COLOR_RGB2BGR,
                )
                writer.write(frame)
        finally:
            writer.release()

    def _build_title_frame(self, title: str, scene_count: int) -> Any:
        modules = self._load_runtime_modules()
        image = modules.image.new("RGB", self.frame_size, color=(17, 20, 28))
        draw = modules.image_draw.Draw(image)
        large_font = modules.image_font.load_default(40)
        medium_font = modules.image_font.load_default(24)
        draw.rectangle((60, 60, 1220, 660), outline=(190, 170, 120), width=3)
        draw.text((100, 120), title.upper(), fill=(235, 226, 202), font=large_font)
        draw.text((100, 190), f"Scenes: {scene_count}", fill=(185, 196, 210), font=medium_font)
        draw.text(
            (100, 230),
            "Generated from bounded /3d lane history and observational captures.",
            fill=(185, 196, 210),
            font=medium_font,
        )
        draw.text(
            (100, 560),
            "Story Forge Movie Renderer",
            fill=(120, 132, 146),
            font=medium_font,
        )
        return image

    def _build_scene_frame(self, scene: MovieScene) -> Any:
        modules = self._load_runtime_modules()
        background = self._scene_background(scene)
        draw = modules.image_draw.Draw(background)
        title_font = modules.image_font.load_default(28)
        body_font = modules.image_font.load_default(20)
        small_font = modules.image_font.load_default(16)

        draw.rounded_rectangle((48, 48, 1232, 672), radius=32, fill=(10, 12, 18, 214), outline=(188, 176, 138), width=2)
        draw.text((86, 82), scene.heading, fill=(243, 235, 214), font=title_font)
        draw.text((86, 120), f"Shot: {scene.shot_type.title()} | Duration: {scene.duration_estimate}", fill=(164, 182, 204), font=small_font)
        draw.text((86, 150), f"Tick: {scene.tick} | Narrative Score: {scene.narrative_score}", fill=(164, 182, 204), font=small_font)

        y = 210
        for line in _wrap_text(scene.lumen_narration, width=78)[:12]:
            draw.text((86, y), line, fill=(240, 240, 236), font=body_font)
            y += 28

        if scene.visual_direction:
            y += 20
            draw.text((86, y), "Visual Direction", fill=(202, 190, 154), font=small_font)
            y += 26
            for line in _wrap_text(scene.visual_direction, width=88)[:8]:
                draw.text((86, y), line, fill=(186, 196, 206), font=small_font)
                y += 22

        if scene.visual_hooks:
            y += 12
            draw.text((86, y), "Continuity Hooks", fill=(202, 190, 154), font=small_font)
            y += 24
            for line in _wrap_text(", ".join(scene.visual_hooks), width=88)[:3]:
                draw.text((86, y), line, fill=(186, 196, 206), font=small_font)
                y += 20

        renderable_capture_count = sum(
            1
            for detail in scene.capture_details
            if str(detail.get("renderable_image_path", "")).strip()
        )

        footer = " | ".join(
            part
            for part in [
                f"Transitions: {', '.join(scene.transition_ids[:2])}" if scene.transition_ids else "",
                f"Captures: {len(scene.capture_references)}",
                f"Renderable: {renderable_capture_count}" if scene.capture_references else "",
            ]
            if part
        )
        draw.text((86, 634), footer or "No transition references", fill=(127, 139, 154), font=small_font)
        return background

    def _scene_background(self, scene: MovieScene) -> Any:
        modules = self._load_runtime_modules()
        capture_image = self._load_capture_background(scene.capture_details)
        if capture_image is not None:
            return capture_image.resize(self.frame_size).convert("RGB")

        digest = hashlib.sha256(
            f"{scene.heading}|{scene.scene_graph_handle}|{scene.shot_type}".encode("utf-8")
        ).digest()
        base = modules.image.new(
            "RGB",
            self.frame_size,
            color=(digest[0] // 2, digest[1] // 3, digest[2] // 4),
        )
        draw = modules.image_draw.Draw(base)
        top = (digest[3], digest[4], digest[5])
        bottom = (digest[6], digest[7], digest[8])
        height = self.frame_size[1]
        width = self.frame_size[0]
        for y in range(height):
            ratio = y / max(1, height - 1)
            color = tuple(
                int(top[index] * (1.0 - ratio) + bottom[index] * ratio)
                for index in range(3)
            )
            draw.line((0, y, width, y), fill=color)
        for step in range(0, width, 140):
            draw.line((step, 0, width - step // 2, height), fill=(255, 255, 255, 18), width=2)
        return base

    def _load_capture_background(self, capture_details: list[dict[str, Any]]) -> Any | None:
        modules = self._load_runtime_modules()
        for detail in capture_details:
            image_path = str(detail.get("renderable_image_path", "") or "").strip()
            if not image_path:
                continue
            path = Path(image_path)
            try:
                return modules.image.open(path).convert("RGB")
            except OSError:
                continue
        return None

    def _write_metadata(
        self,
        path: Path,
        title: str,
        render_id: str,
        state: StoryState,
        lane_entry: dict[str, Any],
        scenes: list[MovieScene],
        video_path: Path,
        frames_dir: Path,
        presentation_mode: str,
    ) -> None:
        payload = {
            "title": title,
            "render_id": render_id,
            "session_id": state.session_id,
            "player_id": state.player_id,
            "world_pack_id": state.world_pack_id,
            "runtime_lane": TEXT_TO_3D_WORLD_LANE_ID,
            "world_id": lane_entry.get("worldId"),
            "engine_provider": lane_entry.get("engineProvider"),
            "scene_count": len(scenes),
            "presentation_mode": presentation_mode,
            "narration_source": (
                MOVIE_PRESENTATION_LUMEN
                if scenes and all(scene.narration_source == MOVIE_PRESENTATION_LUMEN for scene in scenes)
                else MOVIE_PRESENTATION_BACKEND
            ),
            "source_history_entries": len(self._history_entries(state)),
            "video_path": str(video_path),
            "frames_dir": str(frames_dir),
            "video_format": "mp4",
            "video_codec": "mp4v",
            "frame_size": {"width": self.frame_size[0], "height": self.frame_size[1]},
            "fps": self.fps,
            "visual_memory": {
                "artifact_ids": list(state.visual_memory.artifact_ids),
                "hook_state": dict(state.visual_memory.hook_state),
                "last_recall_artifact_ids": list(state.visual_memory.last_recall_artifact_ids),
            },
            "scenes": [
                {
                    "scene_number": scene.scene_number,
                    "heading": scene.heading,
                    "shot_type": scene.shot_type,
                    "duration_estimate": scene.duration_estimate,
                    "capture_references": list(scene.capture_references),
                    "capture_details": list(scene.capture_details),
                    "transition_ids": list(scene.transition_ids),
                    "scene_graph_handle": scene.scene_graph_handle,
                    "tick": scene.tick,
                    "narrative_score": scene.narrative_score,
                    "narration_source": scene.narration_source,
                }
                for scene in scenes
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _resolve_capture_reference(self, reference: str) -> dict[str, Any]:
        path = Path(reference)
        detail = {
            "reference": reference,
            "kind": "missing",
            "renderable_image_path": "",
            "provider": "",
            "event_id": "",
            "event_type": "",
            "approved_visual_hooks": [],
        }
        if not path.exists():
            return detail
        if path.suffix.lower() in _SUPPORTED_CAPTURE_IMAGE_SUFFIXES:
            detail["kind"] = "image_file"
            detail["renderable_image_path"] = str(path)
            return detail
        if path.suffix.lower() != ".json":
            detail["kind"] = "unsupported_file"
            return detail
        payload = self._read_capture_payload(path)
        if payload is None:
            detail["kind"] = "unreadable_json"
            return detail

        detail["kind"] = "artifact_json"
        detail["provider"] = str(
            payload.get("provider") or payload.get("engineProvider") or ""
        ).strip()
        event = payload.get("event", {})
        if isinstance(event, dict):
            detail["event_id"] = str(event.get("eventId", "") or "").strip()
            detail["event_type"] = str(event.get("type", "") or "").strip()
        detail["approved_visual_hooks"] = self._approved_hooks_from_mapping(payload)
        renderable_path = self._renderable_image_path_from_payload(payload, base_dir=path.parent)
        if renderable_path is not None:
            detail["kind"] = "artifact_json_image"
            detail["renderable_image_path"] = renderable_path
        return detail

    def _read_capture_payload(self, path: Path) -> dict[str, Any] | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _renderable_image_path_from_payload(
        self,
        payload: dict[str, Any],
        *,
        base_dir: Path,
    ) -> str | None:
        containers = [
            payload,
            payload.get("data", {}),
            payload.get("artifact", {}),
            payload.get("capture", {}),
            payload.get("metadata", {}),
            payload.get("image", {}),
        ]
        image_keys = (
            "image_path",
            "imagePath",
            "renderable_image_path",
            "renderableImagePath",
            "source_image_path",
            "sourceImagePath",
            "preview_image_path",
            "previewImagePath",
        )
        for container in containers:
            if not isinstance(container, dict):
                continue
            for key in image_keys:
                candidate = str(container.get(key, "") or "").strip()
                if not candidate:
                    continue
                candidate_path = Path(candidate)
                if not candidate_path.is_absolute():
                    candidate_path = (base_dir / candidate_path).resolve()
                if (
                    candidate_path.exists()
                    and candidate_path.suffix.lower() in _SUPPORTED_CAPTURE_IMAGE_SUFFIXES
                ):
                    return str(candidate_path)
        return None

    def _approved_hooks_from_mapping(self, mapping: dict[str, Any]) -> list[str]:
        hooks: list[str] = []
        containers = [
            mapping,
            mapping.get("event", {}),
            mapping.get("visual", {}),
            mapping.get("metadata", {}),
            mapping.get("presentation", {}),
        ]
        hook_keys = (
            "presentation_hooks",
            "approved_presentation_hooks",
            "approvedPresentationHooks",
            "visual_hooks",
            "visualHooks",
            "continuity_hooks",
            "continuityHooks",
        )
        for container in containers:
            if not isinstance(container, dict):
                continue
            for key in hook_keys:
                value = container.get(key)
                if isinstance(value, str):
                    hooks.extend(part.strip() for part in value.split(","))
                elif isinstance(value, (list, tuple, set)):
                    hooks.extend(str(item) for item in value)
        return unique_tokens(hooks)
