from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from assembler.assemble_movie import assemble_movie, verify_ffmpeg
from assembler.contracts import AssemblyRequest
from audio_pipeline.contracts import FullPipelineRequest, FullPipelineResult
from audio_pipeline.orchestrator import AudioPipelineOrchestrator
from speakers.contracts import BusConfig, DuckingRule, RenderTarget, SpeakersMixPlan
from speakers.mix_lane import render_final_mix_from_plan


logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_entry(stage: int, name: str, data: dict) -> str:
    raw = json.dumps({"stage": stage, "name": name, "data": data}, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class FullPipelineRunner:
    def __init__(
        self,
        orchestrator: Optional[AudioPipelineOrchestrator] = None,
        output_root: str = ".runtime-audio",
    ) -> None:
        self._output_root = Path(output_root)
        self._orchestrator = orchestrator or AudioPipelineOrchestrator.from_env(output_root=output_root)

    @classmethod
    def from_env(cls, output_root: str = ".runtime-audio") -> "FullPipelineRunner":
        return cls(output_root=output_root)

    def run(self, request: FullPipelineRequest) -> FullPipelineResult:
        video_path = Path(request.video_path)
        if not video_path.exists():
            return FullPipelineResult.failure(
                request,
                error_type="InputError",
                message="Video path does not exist",
                details={"video_path": str(video_path)},
            )

        audio_result = self._orchestrator.run(request.presented_output)
        audit = list(audio_result.audit)
        if not audio_result.ok or audio_result.mix_plan is None:
            return FullPipelineResult.failure(
                request,
                error_type=audio_result.error_type or "AudioPipelineError",
                message=audio_result.message or "Audio pipeline failed",
                details=audio_result.details,
                audit=audit,
            )

        mix_plan = audio_result.mix_plan
        self._apply_mix_defaults(mix_plan, request)
        previous_hash = audit[-1]["output_hash"] if audit else None

        try:
            final_audio_path = render_final_mix_from_plan(mix_plan, str(self._output_root))
            stage_hash = _hash_entry(
                6,
                "SpeakersFinalMix",
                {"audio_path": final_audio_path, "mix_version": mix_plan.mix_version},
            )
            audit.append(self._entry(6, "SpeakersFinalMix", "passed", stage_hash, previous_hash))
            previous_hash = stage_hash
        except Exception as exc:  # noqa: BLE001
            logger.error("Full pipeline mix render failed for session=%s: %s", request.presented_output.session_id, exc)
            return FullPipelineResult.failure(
                request,
                error_type="MixRenderError",
                message="Final audio mix failed",
                details={"exception": str(exc)},
                audit=audit,
                mix_plan=mix_plan,
            )

        movie_output_path = self._movie_output_path(request)
        assembly_request = AssemblyRequest(
            session_id=request.presented_output.session_id,
            story_id=request.presented_output.story_id,
            run_id=request.presented_output.run_id,
            video_path=str(video_path),
            audio_path=final_audio_path,
            output_path=str(movie_output_path),
            container=request.container,
            video_codec=request.video_codec,
            audio_codec=request.audio_codec,
            audio_bitrate=request.audio_bitrate,
            fps=request.fps,
        )

        ffmpeg_available, ffmpeg_path = verify_ffmpeg()
        if not ffmpeg_available:
            stage_hash = _hash_entry(
                7,
                "AssemblerMovie",
                {"status": "blocked", "reason": "ffmpeg_missing", "output_path": str(movie_output_path)},
            )
            audit.append(self._entry(7, "AssemblerMovie", "blocked", stage_hash, previous_hash))
            return FullPipelineResult.failure(
                request,
                error_type="MissingDependency",
                message="Audio pipeline complete, but ffmpeg is missing for movie assembly",
                details={
                    "dependency": "ffmpeg",
                    "output_path": str(movie_output_path),
                },
                audit=audit,
                mix_plan=mix_plan,
                final_audio_path=final_audio_path,
            )

        try:
            movie_path = assemble_movie(assembly_request)
            stage_hash = _hash_entry(
                7,
                "AssemblerMovie",
                {"movie_path": movie_path, "container": request.container, "ffmpeg": ffmpeg_path},
            )
            audit.append(self._entry(7, "AssemblerMovie", "passed", stage_hash, previous_hash))
        except Exception as exc:  # noqa: BLE001
            logger.error("Full pipeline assembly failed for session=%s: %s", request.presented_output.session_id, exc)
            return FullPipelineResult.failure(
                request,
                error_type="AssemblyError",
                message="Movie assembly failed",
                details={"exception": str(exc), "output_path": str(movie_output_path)},
                audit=audit,
                mix_plan=mix_plan,
                final_audio_path=final_audio_path,
            )

        return FullPipelineResult.success(
            request=request,
            mix_plan=mix_plan,
            final_audio_path=final_audio_path,
            movie_path=movie_path,
            audit=audit,
        )

    def _apply_mix_defaults(self, mix_plan: SpeakersMixPlan, request: FullPipelineRequest) -> None:
        mix_plan.scene_id = mix_plan.scene_id or request.presented_output.scene_id
        mix_plan.mix_version = request.mix_version
        mix_plan.buses.setdefault("master", BusConfig(target_lufs=request.target_lufs, peak_ceiling_db=request.peak_ceiling_db))
        mix_plan.buses.setdefault("music", BusConfig(target_lufs=request.target_lufs - 4.0, peak_ceiling_db=request.peak_ceiling_db - 1.0))
        mix_plan.buses.setdefault("voice", BusConfig(target_lufs=request.target_lufs - 2.0, peak_ceiling_db=request.peak_ceiling_db))

        if not mix_plan.ducking_rules:
            mix_plan.ducking_rules.append(
                DuckingRule(
                    rule_id="voice_ducks_music",
                    when_source="voice",
                    affects="music",
                    duck_amount_db=request.duck_amount_db,
                    attack_ms=50,
                    release_ms=250,
                )
            )

        if not mix_plan.render_targets:
            mix_plan.render_targets.append(
                RenderTarget(
                    target_id="wav_master",
                    format=request.mix_format,
                    sample_rate=request.sample_rate,
                    bit_depth=request.bit_depth,
                    channels=request.channels,
                    filename_pattern=request.mix_filename_pattern,
                )
            )

    def _movie_output_path(self, request: FullPipelineRequest) -> Path:
        if request.movie_output_path:
            return Path(request.movie_output_path)
        apo = request.presented_output
        return self._output_root / apo.session_id / "output" / f"{apo.story_id}_{apo.run_id}_final_movie.{request.container}"

    def _entry(
        self,
        stage: int,
        name: str,
        status: str,
        output_hash: str,
        previous_hash: Optional[str],
    ) -> dict[str, Optional[str] | int]:
        return {
            "stage": stage,
            "name": name,
            "status": status,
            "timestamp": _now(),
            "output_hash": output_hash,
            "prev_hash": previous_hash,
        }
