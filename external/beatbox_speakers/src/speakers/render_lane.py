from __future__ import annotations

import io
import json
import logging
import wave
from pathlib import Path
from typing import Optional

from speakers.adapters import build_speaker_adapter_from_env
from speakers.adapters.base_adapter import SpeakerAdapter
from speakers.contracts import SpeakersMixPlan, SpeakersVoicePlan, StemEntry, TimingEntry


logger = logging.getLogger(__name__)

_SAMPLE_RATE = 44100
_PACE_TO_RATE = {
    "slow": 0.85,
    "normal": 1.0,
    "fast": 1.2,
}


class SpeakerRenderLane:
    def __init__(self, adapter: Optional[SpeakerAdapter] = None) -> None:
        self._adapter = adapter or build_speaker_adapter_from_env()

    def render(
        self,
        voice_plan: SpeakersVoicePlan,
        beatbox_duration_seconds: float,
        output_path: str = "",
    ) -> SpeakersMixPlan:
        output_dir = self._resolve_dir(voice_plan.session_id, output_path)
        if not voice_plan.lines:
            return self._empty_plan(voice_plan, beatbox_duration_seconds, output_dir)

        profile_index = {profile.character_id: profile for profile in voice_plan.voices}
        timing_map: list[TimingEntry] = []
        voice_segments: list[tuple[int, bytes]] = []
        max_voice_end = voice_plan.total_duration_seconds

        for line in voice_plan.lines:
            profile = profile_index.get(line.character_id)
            if profile is None:
                logger.warning("Speakers: missing profile for character_id=%s", line.character_id)
                continue

            speaking_rate = profile.base_rate * _PACE_TO_RATE.get(line.pace, 1.0)
            result = self._adapter.execute(
                "synthesize",
                {
                    "text": line.text,
                    "voice_profile_id": profile.voice_profile_id,
                    "speaking_rate": speaking_rate,
                    "pitch_shift": profile.base_pitch_shift,
                },
            )
            if not result.get("ok"):
                logger.warning(
                    "Speakers: failed to synthesize line %s: %s",
                    line.line_id,
                    result.get("message"),
                )
                continue

            audio_bytes = bytes(result["audio_bytes"])
            pcm, sample_rate = self._extract_pcm(audio_bytes)
            if sample_rate != _SAMPLE_RATE:
                logger.warning("Speakers: unexpected sample rate %s for line %s", sample_rate, line.line_id)
            start_sample = int(line.start_offset_hint_seconds * _SAMPLE_RATE)
            voice_segments.append((start_sample, pcm))
            duration_seconds = float(result.get("duration_seconds", line.estimated_duration_seconds or 0.5))
            max_voice_end = max(max_voice_end, line.start_offset_hint_seconds + duration_seconds)
            timing_map.append(
                TimingEntry(
                    shot_number=line.shot_number,
                    line_id=line.line_id,
                    stem_type="voice",
                    cue_start_seconds=line.start_offset_hint_seconds,
                    duration_seconds=duration_seconds,
                    voice_profile_id=profile.voice_profile_id,
                    text_preview=line.text[:40],
                )
            )

        stem_duration = max(beatbox_duration_seconds, max_voice_end)
        total_samples = max(1, int(stem_duration * _SAMPLE_RATE))
        stem_buffer = bytearray(total_samples * 2)
        for start_sample, pcm in voice_segments:
            start_byte = start_sample * 2
            end_byte = min(len(stem_buffer), start_byte + len(pcm))
            stem_buffer[start_byte:end_byte] = pcm[: end_byte - start_byte]

        voice_path = output_dir / f"{voice_plan.session_id}_voice_stem.wav"
        self._write_wav(voice_path, bytes(stem_buffer))
        timing_path = output_dir / f"{voice_plan.session_id}_voice_timing.json"
        self._write_timing(timing_path, voice_plan, timing_map, stem_duration)

        return SpeakersMixPlan(
            session_id=voice_plan.session_id,
            story_id=voice_plan.story_id,
            run_id=voice_plan.run_id,
            mix_version="voice-stem-v1",
            buses={},
            scene_id=voice_plan.lines[0].scene_id if voice_plan.lines else "",
            voice_stem=StemEntry(
                stem_type="voice",
                file_path=str(voice_path),
                duration_seconds=stem_duration,
                provider=self._adapter.provider_name,
            ),
            timing_map=timing_map,
            total_duration_seconds=stem_duration,
            continuity_passed=self._check_continuity(timing_map),
        )

    def _extract_pcm(self, wav_bytes: bytes) -> tuple[bytes, int]:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            pcm = wav_file.readframes(wav_file.getnframes())
        return pcm, sample_rate

    def _write_wav(self, path: Path, pcm: bytes) -> None:
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(_SAMPLE_RATE)
            wav_file.writeframes(pcm)

    def _write_timing(
        self,
        path: Path,
        plan: SpeakersVoicePlan,
        timing_map: list[TimingEntry],
        stem_duration: float,
    ) -> None:
        payload = {
            "session_id": plan.session_id,
            "story_id": plan.story_id,
            "run_id": plan.run_id,
            "stem_duration_seconds": stem_duration,
            "line_count": len(timing_map),
            "entries": [
                {
                    "shot_number": entry.shot_number,
                    "line_id": entry.line_id,
                    "cue_start_seconds": round(entry.cue_start_seconds, 3),
                    "duration_seconds": round(entry.duration_seconds, 3),
                    "voice_profile_id": entry.voice_profile_id,
                    "text_preview": entry.text_preview,
                }
                for entry in timing_map
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _check_continuity(self, timing_map: list[TimingEntry]) -> bool:
        by_profile: dict[str, list[tuple[float, float]]] = {}
        for entry in timing_map:
            by_profile.setdefault(entry.voice_profile_id, []).append(
                (entry.cue_start_seconds, entry.cue_start_seconds + entry.duration_seconds)
            )
        for profile_id, intervals in by_profile.items():
            ordered = sorted(intervals)
            for idx in range(1, len(ordered)):
                if ordered[idx][0] < ordered[idx - 1][1] - 0.05:
                    logger.warning("Speakers: overlap detected for profile %s", profile_id)
                    return False
        return True

    def _resolve_dir(self, session_id: str, output_path: str) -> Path:
        path = Path(output_path) if output_path else Path(".runtime-speakers") / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _empty_plan(
        self,
        plan: SpeakersVoicePlan,
        duration: float,
        output_dir: Path,
    ) -> SpeakersMixPlan:
        voice_path = output_dir / f"{plan.session_id}_voice_stem.wav"
        silence = bytes(max(1, int(duration * _SAMPLE_RATE)) * 2)
        self._write_wav(voice_path, silence)
        timing_path = output_dir / f"{plan.session_id}_voice_timing.json"
        timing_path.write_text(
            json.dumps(
                {
                    "session_id": plan.session_id,
                    "story_id": plan.story_id,
                    "run_id": plan.run_id,
                    "entries": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return SpeakersMixPlan(
            session_id=plan.session_id,
            story_id=plan.story_id,
            run_id=plan.run_id,
            mix_version="voice-stem-v1",
            buses={},
            scene_id=plan.lines[0].scene_id if plan.lines else "",
            voice_stem=StemEntry(
                stem_type="voice",
                file_path=str(voice_path),
                duration_seconds=duration,
                provider=self._adapter.provider_name,
            ),
            total_duration_seconds=duration,
            continuity_passed=True,
        )
