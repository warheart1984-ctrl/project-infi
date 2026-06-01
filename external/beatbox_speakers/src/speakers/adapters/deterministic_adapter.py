from __future__ import annotations

import io
import math
import struct
import wave
from typing import Any

from speakers.adapters.base_adapter import SpeakerAdapter


_WPS = 2.3
_SAMPLE_RATE = 44100
_VOICE_FREQ: dict[str, float] = {
    "voice_lead_calm_01": 220.0,
    "voice_antagonist_intense_01": 196.0,
    "voice_support_warm_01": 261.6,
    "voice_neutral_01": 233.1,
    "narrator_primary": 246.9,
    "hero_voice": 220.0,
    "narrator_voice": 246.9,
}
_DEFAULT_FREQ = 233.1
_AVAILABLE_PROFILES = sorted(_VOICE_FREQ.keys())


def _estimate_duration(text: str, speaking_rate: float = 1.0) -> float:
    words = len(text.split())
    effective_rate = max(0.3, float(speaking_rate))
    return max(0.5, words / (_WPS * effective_rate))


def _synthesize_wav(
    text: str,
    voice_profile_id: str,
    speaking_rate: float = 1.0,
) -> tuple[bytes, float]:
    freq = _VOICE_FREQ.get(voice_profile_id, _DEFAULT_FREQ)
    duration = _estimate_duration(text, speaking_rate=speaking_rate)
    n_samples = int(duration * _SAMPLE_RATE)
    amplitude = 0.35
    frames: list[bytes] = []

    for i in range(n_samples):
        t = i / _SAMPLE_RATE
        sample = amplitude * (
            math.sin(2 * math.pi * freq * t) * 0.65
            + math.sin(2 * math.pi * freq * 2 * t) * 0.25
            + math.sin(2 * math.pi * freq * 0.5 * t) * 0.10
        )
        fade = min(int(0.05 * _SAMPLE_RATE), max(1, n_samples // 4))
        if i < fade:
            sample *= i / fade
        elif i > n_samples - fade:
            sample *= max(0.0, (n_samples - i) / fade)
        sample = max(-1.0, min(1.0, sample))
        frames.append(struct.pack("<h", int(sample * 32767)))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(_SAMPLE_RATE)
        wav.writeframes(b"".join(frames))
    return buf.getvalue(), duration


class DeterministicSpeakerAdapter(SpeakerAdapter):
    provider_name = "deterministic"

    def _execute_inner(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action == "synthesize":
            return self._synthesize(payload)
        if action == "list_voices":
            return {"ok": True, "profiles": _AVAILABLE_PROFILES}
        raise ValueError(f"Unknown action: {action}")

    def _synthesize(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = payload["text"].strip()
        profile_id = payload.get("voice_profile_id", "voice_neutral_01")
        speaking_rate = payload.get("speaking_rate", 1.0)
        audio_bytes, duration = _synthesize_wav(
            text,
            profile_id,
            speaking_rate=float(speaking_rate),
        )
        return {
            "ok": True,
            "audio_bytes": audio_bytes,
            "duration_seconds": duration,
            "sample_rate": _SAMPLE_RATE,
            "channels": 1,
        }
