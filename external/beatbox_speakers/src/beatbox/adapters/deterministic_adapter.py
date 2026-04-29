"""
Beatbox — Deterministic Adapter
Template-based fallback. No API key required. Always works.
"""
from __future__ import annotations

from typing import Any

from beatbox.adapters.base_adapter import BeatboxAdapter
from beatbox.music_engine import (
    FALLBACK_VOCAL_PATTERNS,
    LYRIC_TEMPLATES,
    build_lyrics,
)


class DeterministicAdapter(BeatboxAdapter):
    """
    Zero-dependency fallback adapter.
    Uses template-based lyrics and deterministic vocal patterns.
    Always returns valid output.
    """

    provider_name = "deterministic"

    def _execute_inner(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action == "generate_lyrics":
            return self._generate_lyrics(payload)
        if action == "generate_vocals":
            return self._generate_vocals(payload)
        if action == "analyze_emotion":
            return self._analyze_emotion(payload)
        # Should never reach here — base class validates actions
        raise ValueError(f"Unknown action: {action}")

    def _generate_lyrics(self, payload: dict[str, Any]) -> dict[str, Any]:
        mood = payload.get("mood", "calm")
        description = payload.get("description", "")
        tone = payload.get("tone", "dark_fantasy")
        lines = build_lyrics(mood, description, tone)
        return {"ok": True, "lines": lines}

    def _generate_vocals(self, payload: dict[str, Any]) -> dict[str, Any]:
        mood = payload.get("mood", "calm")
        notes = FALLBACK_VOCAL_PATTERNS.get(mood, FALLBACK_VOCAL_PATTERNS["calm"])
        # Return copies so callers can't mutate the template
        return {"ok": True, "notes": [dict(n) for n in notes]}

    def _analyze_emotion(self, payload: dict[str, Any]) -> dict[str, Any]:
        # In score mode this is driven by shot data, not audio.
        # Return neutral defaults.
        return {
            "ok": True,
            "emotion": "neutral",
            "energy": 55.0,
            "stress": 35.0,
            "focus": 60.0,
            "valence": 0.5,
            "confidence": 0.8,
        }
