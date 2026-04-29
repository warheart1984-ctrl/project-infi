from __future__ import annotations

import wave
from pathlib import Path
from typing import Dict, Optional

from speakers.adapters import build_speaker_adapter_from_env
from speakers.adapters.base_adapter import SpeakerAdapter
from speakers.contracts import SpeakersVoicePlan, VoiceLine


_PACE_MULTIPLIER = {
    "slow": 1.2,
    "normal": 1.0,
    "fast": 0.82,
}


def _estimate_duration_seconds(line: VoiceLine, base_rate: float) -> float:
    tokens = max(1, len(line.text.split()))
    emphasis_bonus = 0.08 * len(line.emphasis_tokens)
    speech_seconds = (tokens * 0.28 * _PACE_MULTIPLIER.get(line.pace, 1.0)) / max(base_rate, 0.1)
    return max(0.5, speech_seconds + line.pause_after_seconds + emphasis_bonus)


def _write_silence_wav(out_path: Path, duration_seconds: float, sample_rate: int = 44100) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = max(1, int(duration_seconds * sample_rate))
    silence = b"\x00\x00" * frame_count
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(silence)


def _speaking_rate(line: VoiceLine, base_rate: float) -> float:
    return max(0.3, base_rate / _PACE_MULTIPLIER.get(line.pace, 1.0))


def _tts_synthesize(
    line: VoiceLine,
    voice_profile_id: str,
    out_path: Path,
    *,
    base_rate: float,
    adapter: SpeakerAdapter,
) -> None:
    """
    TTS hook with deterministic fallback.
    Writes provider audio bytes when available, or silence if synthesis fails.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = adapter.execute(
        "synthesize",
        {
            "text": line.text,
            "voice_profile_id": voice_profile_id,
            "speaking_rate": _speaking_rate(line, base_rate),
        },
    )
    if result.get("ok"):
        out_path.write_bytes(bytes(result["audio_bytes"]))
        return
    duration_seconds = _estimate_duration_seconds(line, base_rate=base_rate)
    _write_silence_wav(out_path, duration_seconds=duration_seconds)


def render_voice_stems(
    plan: SpeakersVoicePlan,
    output_root: str,
    adapter: Optional[SpeakerAdapter] = None,
) -> Dict[str, str]:
    """
    Render per-line voice WAVs and return a manifest:
    { line_id: "/abs/path/to/line.wav" }
    """
    root = Path(output_root)
    manifest: Dict[str, str] = {}
    adapter = adapter or build_speaker_adapter_from_env()

    voice_index = {v.character_id: v for v in plan.voices}

    for line in plan.lines:
        profile = voice_index.get(line.character_id) or voice_index.get("NARRATOR")
        if profile is None:
            raise ValueError(f"No voice profile for character_id={line.character_id}")

        out_path = (
            root
            / plan.session_id
            / "voice"
            / line.scene_id
            / f"{line.line_id}.wav"
        )
        _tts_synthesize(
            line,
            profile.voice_profile_id,
            out_path,
            base_rate=profile.base_rate,
            adapter=adapter,
        )
        manifest[line.line_id] = str(out_path)

    return manifest
