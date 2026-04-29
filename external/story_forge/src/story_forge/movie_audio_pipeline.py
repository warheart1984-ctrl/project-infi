from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

from story_forge.backend_full_build import BackendBuildArtifact
from story_forge.contracts.audio_handoff import (
    AudioPipelineHandoff,
    attach_movie_render_result,
    build_audio_pipeline_handoff,
)


if TYPE_CHECKING:
    from story_forge.movie_renderer import MovieRenderResult


def resolve_audio_pipeline_src(audio_pipeline_src: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if audio_pipeline_src is not None:
        candidates.append(Path(audio_pipeline_src))

    env_path = os.environ.get("STORY_FORGE_AUDIO_PIPELINE_SRC", "").strip()
    if env_path:
        candidates.append(Path(env_path))

    repo_root = Path(__file__).resolve().parents[4]
    candidates.append(repo_root / "external" / "beatbox_speakers" / "src")
    candidates.append(repo_root / "external" / "Beatbox&speakers" / "src")
    candidates.append(repo_root.parent / "Beatbox&speakers" / "src")

    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if (resolved / "audio_pipeline").exists() and (resolved / "speakers").exists():
            return resolved

    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        "Could not locate Beatbox&speakers src directory for Story Forge audio pipeline. "
        f"Searched: {searched}"
    )


def ensure_audio_pipeline_src(audio_pipeline_src: str | Path | None = None) -> Path:
    resolved = resolve_audio_pipeline_src(audio_pipeline_src)
    resolved_str = str(resolved)
    if resolved_str not in sys.path:
        sys.path.insert(0, resolved_str)
    return resolved


@dataclass(slots=True)
class StoryForgeMovieAudioPipelineRun:
    handoff: AudioPipelineHandoff
    request: Any
    result: Any


def build_full_pipeline_request_from_handoff(
    handoff: AudioPipelineHandoff,
    *,
    movie_output_path: str = "",
    mix_version: str = "story-forge-movie-audio-v1",
    mix_filename_pattern: str = "{story_id}_{run_id}_final_mix.wav",
    mix_format: str = "wav",
    sample_rate: int = 44100,
    bit_depth: int = 16,
    channels: int = 1,
    duck_amount_db: float = 8.0,
    target_lufs: float = -16.0,
    peak_ceiling_db: float = -1.0,
    video_codec: str = "libx264",
    audio_codec: str = "aac",
    audio_bitrate: str = "192k",
    fps: int = 24,
    container: str = "mp4",
    audio_pipeline_src: str | Path | None = None,
) -> Any:
    if not handoff.video_path:
        raise ValueError("Audio pipeline handoff is missing a rendered video path.")

    ensure_audio_pipeline_src(audio_pipeline_src)

    from audio_pipeline import FullPipelineRequest, build_audio_presented_output

    presented_output = build_audio_presented_output(
        session_id=handoff.session_id,
        story_id=handoff.story_id,
        run_id=handoff.run_id,
        scene_id=handoff.scene_id,
        shots=deepcopy(handoff.shots),
        entities=deepcopy(handoff.entities),
        tone=handoff.tone,
        target=handoff.target,
        screenplay=handoff.screenplay,
        dialogue_lines=deepcopy(handoff.dialogue_lines),
        narration_lines=deepcopy(handoff.narration_lines),
        metadata=deepcopy(handoff.metadata),
    )

    return FullPipelineRequest(
        presented_output=presented_output,
        video_path=handoff.video_path,
        movie_output_path=movie_output_path,
        mix_version=mix_version,
        mix_filename_pattern=mix_filename_pattern,
        mix_format=mix_format,
        sample_rate=sample_rate,
        bit_depth=bit_depth,
        channels=channels,
        duck_amount_db=duck_amount_db,
        target_lufs=target_lufs,
        peak_ceiling_db=peak_ceiling_db,
        video_codec=video_codec,
        audio_codec=audio_codec,
        audio_bitrate=audio_bitrate,
        fps=fps,
        container=container,
    )


def run_story_forge_movie_audio_pipeline(
    artifact: BackendBuildArtifact,
    *,
    movie_result: "MovieRenderResult" | None = None,
    video_path: str | None = None,
    output_root: str | Path = ".runtime-audio",
    movie_output_path: str = "",
    runner: Any | None = None,
    audio_pipeline_src: str | Path | None = None,
    mix_version: str = "story-forge-movie-audio-v1",
    mix_filename_pattern: str = "{story_id}_{run_id}_final_mix.wav",
    mix_format: str = "wav",
    sample_rate: int = 44100,
    bit_depth: int = 16,
    channels: int = 1,
    duck_amount_db: float = 8.0,
    target_lufs: float = -16.0,
    peak_ceiling_db: float = -1.0,
    video_codec: str = "libx264",
    audio_codec: str = "aac",
    audio_bitrate: str = "192k",
    fps: int = 24,
    container: str = "mp4",
) -> StoryForgeMovieAudioPipelineRun:
    ensure_audio_pipeline_src(audio_pipeline_src)

    handoff = build_audio_pipeline_handoff(artifact, video_path=video_path)
    if movie_result is not None:
        handoff = attach_movie_render_result(handoff, movie_result)
    if not handoff.video_path:
        raise ValueError(
            "Story Forge movie audio pipeline requires a rendered movie video path. "
            "Provide movie_result or video_path."
        )

    request = build_full_pipeline_request_from_handoff(
        handoff,
        movie_output_path=movie_output_path,
        mix_version=mix_version,
        mix_filename_pattern=mix_filename_pattern,
        mix_format=mix_format,
        sample_rate=sample_rate,
        bit_depth=bit_depth,
        channels=channels,
        duck_amount_db=duck_amount_db,
        target_lufs=target_lufs,
        peak_ceiling_db=peak_ceiling_db,
        video_codec=video_codec,
        audio_codec=audio_codec,
        audio_bitrate=audio_bitrate,
        fps=fps,
        container=container,
        audio_pipeline_src=audio_pipeline_src,
    )

    pipeline_runner = runner
    if pipeline_runner is None:
        from audio_pipeline import FullPipelineRunner

        pipeline_runner = FullPipelineRunner.from_env(output_root=str(output_root))

    result = pipeline_runner.run(request)
    return StoryForgeMovieAudioPipelineRun(
        handoff=handoff,
        request=request,
        result=result,
    )


run_movie_audio_pipeline = run_story_forge_movie_audio_pipeline
