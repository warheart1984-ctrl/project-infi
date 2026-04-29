from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from speakers.adapters.base_adapter import SpeakerAdapter, SpeakerAdapterError
from speakers.adapters.deterministic_adapter import DeterministicSpeakerAdapter, _synthesize_wav


_DEFAULT_VOICE_MAP: dict[str, str] = {
    "voice_lead_calm_01": "21m00Tcm4TlvDq8ikWAM",
    "voice_antagonist_intense_01": "AZnzlk1XvdvUeBnXmlld",
    "voice_support_warm_01": "EXAVITQu4vr4xnSDxMaL",
    "voice_neutral_01": "MF3mGyEYCl7XYWbV9V6O",
    "narrator_primary": "pNInz6obpgDQGcFmaJgB",
}
_EL_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


@dataclass
class ElevenLabsConfig:
    api_key: str
    model_id: str = "eleven_monolingual_v1"
    voice_map: Optional[dict[str, str]] = None
    timeout: int = 30

    def __post_init__(self) -> None:
        if self.voice_map is None:
            self.voice_map = dict(_DEFAULT_VOICE_MAP)
        for profile_id in list(self.voice_map.keys()):
            env_key = f"SPEAKER_EL_VOICE_{profile_id.upper()}"
            override = os.environ.get(env_key)
            if override:
                self.voice_map[profile_id] = override

    @classmethod
    def from_env(cls) -> "ElevenLabsConfig":
        key = (
            os.environ.get("SPEAKER_ELEVENLABS_API_KEY")
            or os.environ.get("ELEVENLABS_API_KEY")
            or ""
        )
        model = os.environ.get("SPEAKER_EL_MODEL", "eleven_monolingual_v1")
        return cls(api_key=key, model_id=model)

    @property
    def available(self) -> bool:
        return bool(self.api_key)


class ElevenLabsAdapter(SpeakerAdapter):
    provider_name = "elevenlabs"

    def __init__(self, config: Optional[ElevenLabsConfig] = None) -> None:
        self._config = config or ElevenLabsConfig.from_env()
        self._fallback = DeterministicSpeakerAdapter()

    def _execute_inner(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._config.available:
            return self._fallback._execute_inner(action, payload)
        if action == "synthesize":
            return self._synthesize(payload)
        if action == "list_voices":
            return {"ok": True, "profiles": list((self._config.voice_map or {}).keys())}
        raise ValueError(f"Unknown action: {action}")

    def _synthesize(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            import requests  # type: ignore[import]
        except ImportError as exc:
            raise SpeakerAdapterError("requests package not installed") from exc

        text = payload["text"].strip()
        profile_id = payload.get("voice_profile_id", "voice_neutral_01")
        voice_id = (self._config.voice_map or {}).get(profile_id)
        if not voice_id:
            raise SpeakerAdapterError(f"No ElevenLabs voice ID for profile: {profile_id!r}")

        response = requests.post(
            _EL_TTS_URL.format(voice_id=voice_id),
            json={
                "text": text,
                "model_id": self._config.model_id,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            headers={
                "xi-api-key": self._config.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            timeout=self._config.timeout,
        )
        if not response.ok:
            raise SpeakerAdapterError(
                f"ElevenLabs API error {response.status_code}: {response.text[:200]}"
            )
        audio_bytes, duration = self._mp3_to_wav(response.content, text)
        return {
            "ok": True,
            "audio_bytes": audio_bytes,
            "duration_seconds": duration,
            "sample_rate": 44100,
            "channels": 1,
        }

    def _mp3_to_wav(self, mp3_bytes: bytes, text: str) -> tuple[bytes, float]:
        try:
            import io
            from pydub import AudioSegment  # type: ignore[import]

            audio = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
            audio = audio.set_frame_rate(44100).set_channels(1)
            buf = io.BytesIO()
            audio.export(buf, format="wav")
            return buf.getvalue(), len(audio) / 1000.0
        except ImportError:
            return _synthesize_wav(text, "voice_neutral_01")
