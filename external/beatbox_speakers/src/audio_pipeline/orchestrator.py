from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from audio_pipeline.contracts import AudioPipelineResult, AudioPresentedOutput
from audio_pipeline.cue_plan_builder import build_cue_plan
from beatbox.lanes.beatbox_lane import BeatboxLane
from speakers.adapters import build_speaker_adapter_from_env
from speakers.adapters.base_adapter import SpeakerAdapter
from speakers.contracts import SpeakersMixPlan, StemEntry
from speakers.render_lane import SpeakerRenderLane
from speakers.voice_plan_builder import build_voice_plan


logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_entry(stage: int, name: str, data: dict) -> str:
    raw = json.dumps({"stage": stage, "name": name, "data": data}, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class AudioPipelineOrchestrator:
    def __init__(
        self,
        speaker_adapter: Optional[SpeakerAdapter] = None,
        beatbox_lane: Optional[BeatboxLane] = None,
        output_root: str = ".runtime-audio",
    ) -> None:
        self._speaker_adapter = speaker_adapter or build_speaker_adapter_from_env()
        self._beatbox_lane = beatbox_lane or BeatboxLane.from_env()
        self._output_root = Path(output_root)
        self._speaker_render = SpeakerRenderLane(self._speaker_adapter)

    @classmethod
    def from_env(cls, output_root: str = ".runtime-audio") -> "AudioPipelineOrchestrator":
        return cls(output_root=output_root)

    def run(self, apo: AudioPresentedOutput) -> AudioPipelineResult:
        audit: list[dict] = []
        previous_hash: Optional[str] = None
        output_dir = self._output_root / apo.session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            cue_plan = build_cue_plan(apo)
            stage_hash = _hash_entry(
                1,
                "BeatboxCuePlan",
                {"cue_count": len(cue_plan.cues), "total_duration": cue_plan.total_duration_seconds},
            )
            audit.append(self._entry(1, "BeatboxCuePlan", "passed", stage_hash, previous_hash))
            previous_hash = stage_hash

            score_request = cue_plan.to_score_request(output_path=str(output_dir))
            beatbox_result = self._beatbox_lane.score(score_request)
            if not beatbox_result.ok or beatbox_result.data is None:
                raise RuntimeError(beatbox_result.message or "BeatBox pipeline failed")
            beatbox_artifact = beatbox_result.data
            stage_hash = _hash_entry(
                2,
                "BeatboxScoreLane",
                {
                    "cue_count": beatbox_artifact.cue_count,
                    "continuity": beatbox_artifact.continuity_passed,
                    "duration": beatbox_artifact.total_duration_seconds,
                },
            )
            audit.append(self._entry(2, "BeatboxScoreLane", "passed", stage_hash, previous_hash))
            previous_hash = stage_hash

            voice_plan = build_voice_plan(apo)
            stage_hash = _hash_entry(
                3,
                "SpeakersVoicePlan",
                {"line_count": len(voice_plan.lines), "duration": voice_plan.total_duration_seconds},
            )
            audit.append(self._entry(3, "SpeakersVoicePlan", "passed", stage_hash, previous_hash))
            previous_hash = stage_hash

            mix_plan = self._speaker_render.render(
                voice_plan,
                beatbox_duration_seconds=beatbox_artifact.total_duration_seconds,
                output_path=str(output_dir),
            )
            mix_plan.music_stem = StemEntry(
                stem_type="music",
                file_path=beatbox_artifact.audio_path,
                duration_seconds=beatbox_artifact.total_duration_seconds,
                provider=beatbox_artifact.provider,
            )
            mix_plan.scene_id = apo.scene_id
            mix_plan.total_duration_seconds = max(
                beatbox_artifact.total_duration_seconds,
                mix_plan.total_duration_seconds,
            )

            stage_hash = _hash_entry(
                4,
                "SpeakerRenderLane",
                {
                    "voice_lines": len(mix_plan.timing_map),
                    "continuity": mix_plan.continuity_passed,
                    "duration": mix_plan.total_duration_seconds,
                },
            )
            audit.append(self._entry(4, "SpeakerRenderLane", "passed", stage_hash, previous_hash))
            previous_hash = stage_hash

            stage_hash = _hash_entry(5, "MixPlanAssembly", mix_plan.to_payload())
            audit.append(self._entry(5, "MixPlanAssembly", "complete", stage_hash, previous_hash))

            self._write_mix_manifest(output_dir, apo, mix_plan, audit)
            return AudioPipelineResult(
                ok=True,
                session_id=apo.session_id,
                story_id=apo.story_id,
                run_id=apo.run_id,
                scene_id=apo.scene_id,
                mix_plan=mix_plan,
                audit=audit,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Audio pipeline failed for session=%s: %s", apo.session_id, exc)
            return AudioPipelineResult.failure(
                session_id=apo.session_id,
                story_id=apo.story_id,
                run_id=apo.run_id,
                scene_id=apo.scene_id,
                error_type="PipelineError",
                message="Audio pipeline failed",
                details={"exception": str(exc), "audit_so_far": len(audit)},
            )

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

    def _write_mix_manifest(
        self,
        output_dir: Path,
        apo: AudioPresentedOutput,
        mix_plan: SpeakersMixPlan,
        audit: list[dict],
    ) -> None:
        payload = {
            "session_id": apo.session_id,
            "story_id": apo.story_id,
            "run_id": apo.run_id,
            "scene_id": apo.scene_id,
            **mix_plan.to_payload(),
            "timing_map": [
                {
                    "shot_number": entry.shot_number,
                    "line_id": entry.line_id,
                    "cue_start_seconds": entry.cue_start_seconds,
                    "duration_seconds": entry.duration_seconds,
                    "voice_profile_id": entry.voice_profile_id,
                    "text_preview": entry.text_preview,
                }
                for entry in mix_plan.timing_map
            ],
            "audit": audit,
        }
        path = output_dir / f"{apo.session_id}_mix_plan.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
