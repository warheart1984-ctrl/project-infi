"""
Beatbox — OpenAI Adapter
Provider adapter for lyrics and vocal generation via OpenAI.
Falls back gracefully when key is absent.
Model: gpt-4o-mini (corrected from gpt-5-mini which does not exist).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from beatbox.adapters.base_adapter import BeatboxAdapter, BeatboxAdapterError
from beatbox.music_engine import FALLBACK_VOCAL_PATTERNS, build_lyrics

_ALLOWED_NOTES = {
    "calm":    {"C4","D4","E4","G4","A4"},
    "focused": {"D4","F4","A4","C5"},
    "intense": {"E4","G4","A4","B4","D5"},
    "happy":   {"G4","A4","C5","D5","E5"},
}


@dataclass
class OpenAIAdapterConfig:
    api_key: str
    model: str = "gpt-4o-mini"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> OpenAIAdapterConfig:
        key = (
            os.environ.get("BEATBOX_OPENAI_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        )
        model = os.environ.get("BEATBOX_OPENAI_MODEL", "gpt-4o-mini")
        return cls(api_key=key, model=model)

    @property
    def available(self) -> bool:
        return bool(self.api_key)


class OpenAIAdapter(BeatboxAdapter):
    """
    OpenAI-backed lyrics and vocal generation.
    Requires BEATBOX_OPENAI_API_KEY or OPENAI_API_KEY.
    Falls back to deterministic output when key is absent.
    """

    provider_name = "openai"

    def __init__(self, config: Optional[OpenAIAdapterConfig] = None) -> None:
        self._config = config or OpenAIAdapterConfig.from_env()

    def _execute_inner(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._config.available:
            # Degrade gracefully — same as deterministic
            return self._deterministic_fallback(action, payload)

        if action == "generate_lyrics":
            return self._generate_lyrics(payload)
        if action == "generate_vocals":
            return self._generate_vocals(payload)
        if action == "analyze_emotion":
            # OpenAI doesn't do audio analysis — use deterministic
            return {"ok": True, "emotion": "neutral", "energy": 55.0,
                    "stress": 35.0, "focus": 60.0, "valence": 0.5, "confidence": 0.8}
        raise ValueError(f"Unknown action: {action}")

    def _generate_lyrics(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            import openai  # type: ignore[import]
        except ImportError as exc:
            raise BeatboxAdapterError("openai package not installed") from exc

        mood = payload.get("mood", "calm")
        description = payload.get("description", "")
        tone = payload.get("tone", "dark_fantasy")
        bpm = payload.get("bpm", 120)

        client = openai.OpenAI(api_key=self._config.api_key)
        prompt = "\n".join([
            "Write 6 short lyrical lines for a cinematic adaptive score.",
            "Each line must be singable and under 10 words.",
            "Keep the language emotionally direct and cinematic.",
            f"Mood: {mood}",
            f"Scene: {description[:80]}",
            f"Tone: {tone}",
            f"BPM: {bpm}",
            'Return strict JSON only: {"lines":["..."]}',
        ])

        response = client.chat.completions.create(
            model=self._config.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=self._config.timeout,
        )
        text = response.choices[0].message.content or "{}"
        parsed = json.loads(text)
        lines = parsed.get("lines", [])

        if not isinstance(lines, list) or not lines:
            return {"ok": True, "lines": build_lyrics(mood, description, tone)}

        return {"ok": True, "lines": [str(l) for l in lines[:8]]}

    def _generate_vocals(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            import openai  # type: ignore[import]
        except ImportError as exc:
            raise BeatboxAdapterError("openai package not installed") from exc

        mood = payload.get("mood", "calm")
        bpm = payload.get("bpm", 120)
        lyrics = payload.get("lyrics", [])
        allowed = sorted(_ALLOWED_NOTES.get(mood, _ALLOWED_NOTES["calm"]))

        client = openai.OpenAI(api_key=self._config.api_key)
        prompt = "\n".join([
            "Create a short singable vocal phrase for a cinematic score.",
            "Return 4 to 8 notes.",
            "Use only the allowed notes listed below.",
            "Each durationBeats must be 0.5, 1, 2, or 4.",
            "Velocity must be 0.2 to 1.0.",
            f"Mood: {mood}",
            f"BPM: {bpm}",
            f"Allowed notes: {', '.join(allowed)}",
            f"Lyrics context: {' | '.join(lyrics[:4])}",
            'Return strict JSON only: {"notes":[{"note":"C4","durationBeats":1,"lyric":"rise","velocity":0.7}]}',
        ])

        response = client.chat.completions.create(
            model=self._config.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=self._config.timeout,
        )
        text = response.choices[0].message.content or "{}"
        parsed = json.loads(text)
        raw_notes = parsed.get("notes", [])
        notes = self._sanitize_notes(raw_notes, mood)

        if not notes:
            return {"ok": True, "notes": list(FALLBACK_VOCAL_PATTERNS.get(mood, FALLBACK_VOCAL_PATTERNS["calm"]))}

        return {"ok": True, "notes": notes}

    def _sanitize_notes(self, raw: Any, mood: str) -> list[dict[str, Any]]:
        allowed = _ALLOWED_NOTES.get(mood, _ALLOWED_NOTES["calm"])
        if not isinstance(raw, list):
            return []
        result = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            note = item.get("note", "C4")
            if note not in allowed:
                note = next(iter(sorted(allowed)))
            duration = max(0.5, min(4.0, float(item.get("durationBeats", 1))))
            velocity = max(0.2, min(1.0, float(item.get("velocity", 0.7))))
            lyric = str(item.get("lyric", ""))[:16] if item.get("lyric") else None
            entry: dict[str, Any] = {"note": note, "durationBeats": duration, "velocity": velocity}
            if lyric:
                entry["lyric"] = lyric
            result.append(entry)
        return result

    def _deterministic_fallback(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from beatbox.adapters.deterministic_adapter import DeterministicAdapter
        return DeterministicAdapter()._execute_inner(action, payload)
