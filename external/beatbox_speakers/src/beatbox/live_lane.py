"""
Beatbox — Live Lane
Adapts game state and player signals into SceneState for real-time music.
This is the Python-side contract layer. The actual audio engine runs in
the browser via Tone.js (see beatbox frontend).
The live lane exposes a state endpoint that the frontend polls.
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Literal, Optional

from beatbox.adapters.base_adapter import BeatboxAdapter
from beatbox.adapters.deterministic_adapter import DeterministicAdapter
from beatbox.contracts import LiveStateUpdate, SceneState
from beatbox.scene_state_builder import (
    _clamp,
    _derive_bpm,
    _derive_mood,
)

logger = logging.getLogger(__name__)


class LiveLane:
    """
    Live mode: converts game state + player signals into SceneState.
    Exposes resolve_state() for the backend to call on each game turn.
    The frontend Tone.js engine polls /api/beatbox/live-state and adapts.
    """

    def __init__(self, adapter: Optional[BeatboxAdapter] = None) -> None:
        self._adapter = adapter or DeterministicAdapter()
        self._last_state: Optional[SceneState] = None

    def resolve_state(self, update: LiveStateUpdate) -> SceneState:
        """
        Derive a SceneState from a LiveStateUpdate.
        Called on every game turn where audio should adapt.
        """
        # Map game intensity to energy
        energy = _clamp(update.intensity, 0.0, 100.0)

        # Map scene emotion to tension + valence
        tension = self._emotion_to_tension(update.scene_emotion)
        valence = self._emotion_to_valence(update.scene_emotion)

        # Blend with player input if present
        if update.player_input_energy > 0:
            energy = _clamp(energy * 0.6 + update.player_input_energy * 0.4, 0.0, 100.0)
        if update.player_input_stress > 0:
            tension = _clamp(tension * 0.6 + update.player_input_stress * 0.4, 0.0, 100.0)

        focus = _clamp(update.player_input_focus, 0.0, 100.0)
        mood = _derive_mood(energy, tension, focus, valence)
        bpm = _derive_bpm(energy, focus, tension, valence)

        state = SceneState(
            energy=energy,
            tension=tension,
            focus=focus,
            valence=valence,
            mood=mood,
            bpm=bpm,
            description=update.scene_emotion,
        )
        self._last_state = state
        return state

    def get_live_payload(self, update: LiveStateUpdate) -> dict[str, Any]:
        """
        Returns the JSON payload the frontend Tone.js engine consumes.
        Called by /api/beatbox/live-state.
        """
        state = self.resolve_state(update)

        # Generate vocals via adapter
        vocal_result = self._adapter.execute("generate_vocals", {
            "mood": state.mood,
            "bpm": state.bpm,
        })
        vocal_notes = vocal_result.get("notes", []) if vocal_result.get("ok") else []

        return {
            "mood": state.mood,
            "bpm": state.bpm,
            "energy": state.energy,
            "tension": state.tension,
            "focus": state.focus,
            "valence": state.valence,
            "vocal_notes": vocal_notes,
            "provider": self._adapter.provider_name,
        }

    # ── Emotion mappings ──────────────────────────────────────────────────────

    _HIGH_TENSION_EMOTIONS = {
        "fear", "dread", "rage", "despair", "grief", "horror",
        "betrayal", "fracture", "dark", "intense",
    }
    _HIGH_VALENCE_EMOTIONS = {
        "joy", "triumph", "hope", "love", "happy", "elation",
        "warmth", "relief", "calm",
    }

    def _emotion_to_tension(self, emotion: str) -> float:
        lower = emotion.lower()
        if any(e in lower for e in self._HIGH_TENSION_EMOTIONS):
            return 80.0
        if any(e in lower for e in self._HIGH_VALENCE_EMOTIONS):
            return 20.0
        return 45.0

    def _emotion_to_valence(self, emotion: str) -> float:
        lower = emotion.lower()
        if any(e in lower for e in self._HIGH_VALENCE_EMOTIONS):
            return 0.75
        if any(e in lower for e in self._HIGH_TENSION_EMOTIONS):
            return 0.25
        return 0.5
