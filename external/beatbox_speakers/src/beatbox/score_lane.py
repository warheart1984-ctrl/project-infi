"""
Beatbox — Score Lane
Fixed timeline renderer for the film pipeline.
Reads ScoreRequest, produces BeatboxArtifact with audio + timeline manifest.
"""
from __future__ import annotations

import json
import logging
import os
import struct
import wave
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from beatbox.adapters.base_adapter import BeatboxAdapter
from beatbox.adapters.deterministic_adapter import DeterministicAdapter
from beatbox.contracts import BeatboxArtifact, MusicCue, ScoreRequest, ShotSceneState
from beatbox.music_engine import build_arrangement, build_cue_from_shot, build_lyrics

logger = logging.getLogger(__name__)


class ScoreLane:
    """
    Score mode: reads a ScoreRequest, generates per-shot music cues,
    assembles a timeline manifest, writes a WAV audio file.
    No API key required — deterministic audio is always available.
    """

    def __init__(self, adapter: Optional[BeatboxAdapter] = None) -> None:
        self._adapter = adapter or DeterministicAdapter()

    def score(self, request: ScoreRequest) -> BeatboxArtifact:
        if not request.shots:
            return self._empty_artifact(request)

        cues: list[MusicCue] = []
        all_lyrics: list[str] = []
        total_duration = 0.0

        for shot_state in request.shots:
            cue = build_cue_from_shot(shot_state)
            cues.append(cue)
            total_duration += shot_state.duration_seconds

            # Generate lyrics for this shot via adapter
            lyric_result = self._adapter.execute("generate_lyrics", {
                "mood": shot_state.scene_state.mood,
                "description": shot_state.scene_state.description,
                "tone": request.tone,
                "bpm": shot_state.scene_state.bpm,
            })
            if lyric_result.get("ok") and lyric_result.get("lines"):
                all_lyrics.extend(lyric_result["lines"][:2])  # 2 lines per shot

        # Verify continuity: cue starts must be non-decreasing
        continuity_passed = self._check_continuity(cues)

        # Write outputs
        output_dir = self._resolve_output_dir(request)
        audio_path = self._write_audio(output_dir, request, cues)
        timeline_path = self._write_timeline(output_dir, request, cues, all_lyrics)

        return BeatboxArtifact(
            session_id=request.session_id,
            scene_id=request.scene_id,
            audio_path=str(audio_path),
            timeline_path=str(timeline_path),
            mode="score",
            provider=self._adapter.provider_name,
            continuity_passed=continuity_passed,
            cue_count=len(cues),
            total_duration_seconds=total_duration,
            cues=cues,
        )

    # ── Continuity ────────────────────────────────────────────────────────────

    def _check_continuity(self, cues: list[MusicCue]) -> bool:
        for i in range(1, len(cues)):
            expected = cues[i - 1].cue_start_seconds + cues[i - 1].duration_seconds
            if abs(cues[i].cue_start_seconds - expected) > 0.01:
                logger.warning(
                    "Beatbox continuity: gap at cue %d (expected %.2fs, got %.2fs)",
                    cues[i].shot_number, expected, cues[i].cue_start_seconds,
                )
                return False
        return True

    # ── Audio Writer ──────────────────────────────────────────────────────────

    def _write_audio(
        self, output_dir: Path, request: ScoreRequest, cues: list[MusicCue]
    ) -> Path:
        """
        Write a deterministic WAV file.
        Each shot gets a sine-wave tone at a frequency derived from its BPM + mood.
        This is the local cinematic equivalent for audio — real output without
        a provider. Provider-backed audio (Suno, ElevenLabs, etc.) can replace
        this via adapter swap at the same seam.
        """
        audio_path = output_dir / f"{request.session_id}_score.wav"
        sample_rate = 44100
        frames: list[bytes] = []

        import math

        for cue in cues:
            n_samples = int(cue.duration_seconds * sample_rate)
            # Frequency: map bpm to a base tone (C=261, range 200–500Hz)
            freq = 200 + (cue.bpm - 70) * (300 / 105)
            # Amplitude: energy → volume (0.1 – 0.8)
            amplitude = 0.1 + (cue.energy / 100) * 0.7
            # Mood detune: intense = slight dissonance
            detune = 1.005 if cue.mood == "intense" else 1.0
            for i in range(n_samples):
                t = i / sample_rate
                # Simple sine wave + harmonic
                sample = amplitude * (
                    math.sin(2 * math.pi * freq * detune * t) * 0.7
                    + math.sin(2 * math.pi * freq * 2 * t) * 0.2
                    + math.sin(2 * math.pi * freq * 0.5 * t) * 0.1
                )
                # Apply simple fade in/out per cue
                fade_samples = min(int(0.05 * sample_rate), n_samples // 4)
                if i < fade_samples:
                    sample *= i / fade_samples
                elif i > n_samples - fade_samples:
                    sample *= (n_samples - i) / fade_samples
                # Clamp and convert to 16-bit PCM
                sample = max(-1.0, min(1.0, sample))
                frames.append(struct.pack("<h", int(sample * 32767)))

        with wave.open(str(audio_path), "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(b"".join(frames))

        logger.info("Beatbox: wrote audio %s (%.1fs)", audio_path.name, sum(c.duration_seconds for c in cues))
        return audio_path

    # ── Timeline Writer ───────────────────────────────────────────────────────

    def _write_timeline(
        self,
        output_dir: Path,
        request: ScoreRequest,
        cues: list[MusicCue],
        lyrics: list[str],
    ) -> Path:
        timeline_path = output_dir / f"{request.session_id}_timeline.json"
        manifest = {
            "session_id": request.session_id,
            "scene_id": request.scene_id,
            "tone": request.tone,
            "target": request.target,
            "total_duration_seconds": sum(c.duration_seconds for c in cues),
            "cue_count": len(cues),
            "lyrics_summary": lyrics[:12],
            "cues": [
                {
                    "shot_number": c.shot_number,
                    "cue_start_seconds": round(c.cue_start_seconds, 3),
                    "duration_seconds": round(c.duration_seconds, 3),
                    "mood": c.mood,
                    "bpm": c.bpm,
                    "energy": round(c.energy, 1),
                    "tension": round(c.tension, 1),
                    "valence": round(c.valence, 3),
                    "description": c.description,
                }
                for c in cues
            ],
        }
        timeline_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info("Beatbox: wrote timeline %s (%d cues)", timeline_path.name, len(cues))
        return timeline_path

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _resolve_output_dir(self, request: ScoreRequest) -> Path:
        if request.output_path:
            p = Path(request.output_path)
        else:
            p = Path(".runtime-beatbox") / request.session_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _empty_artifact(self, request: ScoreRequest) -> BeatboxArtifact:
        output_dir = self._resolve_output_dir(request)
        # Write empty files so downstream Speaker doesn't crash on missing paths
        audio_path = output_dir / f"{request.session_id}_score.wav"
        timeline_path = output_dir / f"{request.session_id}_timeline.json"
        with wave.open(str(audio_path), "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            wav.writeframes(b"")
        timeline_path.write_text(json.dumps({
            "session_id": request.session_id,
            "scene_id": request.scene_id,
            "cues": [],
            "total_duration_seconds": 0.0,
        }), encoding="utf-8")
        return BeatboxArtifact(
            session_id=request.session_id,
            scene_id=request.scene_id,
            audio_path=str(audio_path),
            timeline_path=str(timeline_path),
            mode="score",
            provider=self._adapter.provider_name,
            continuity_passed=True,
            cue_count=0,
            total_duration_seconds=0.0,
            cues=[],
        )
