"""
Beatbox — Scene State Builder
Converts Story Forge TemporalShotList + BackendBuildArtifact into Beatbox contracts.
This is the seam between Story Forge and Beatbox. No Story Forge imports
are required at runtime — it works against plain dicts or dataclasses.
"""
from __future__ import annotations

import math
from typing import Any, Literal

from beatbox.contracts import SceneState, ScoreRequest, ShotSceneState


# ── Mood derivation ───────────────────────────────────────────────────────────

_HIGH_TENSION_KEYWORDS = {
    "harsh", "fracture", "dark", "shatter", "break", "collapse",
    "confront", "betray", "rage", "despair", "grief", "dread",
    "chiaroscuro", "shadow", "isolation",
}
_HIGH_VALENCE_KEYWORDS = {
    "light", "hope", "triumph", "joy", "warmth", "sunrise",
    "resolve", "peace", "tender", "reunion",
}
_FOCUS_INTENTS = {
    "advance central dilemma", "advance", "confront", "decide",
    "escalate", "reveal", "turn",
}
_OBSERVE_INTENTS = {"observe", "establish", "breathe", "rest", "linger"}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _pacing_to_energy(pacing: str) -> float:
    return {"slow": 30.0, "medium": 60.0, "fast": 90.0}.get(pacing, 60.0)


def _visual_intent_to_tension(visual_intent: str) -> float:
    words = set(visual_intent.lower().split())
    hits = len(words & _HIGH_TENSION_KEYWORDS)
    return _clamp(hits * 25.0, 0.0, 100.0)


def _visual_intent_to_valence(visual_intent: str) -> float:
    words = set(visual_intent.lower().split())
    high = len(words & _HIGH_VALENCE_KEYWORDS)
    low = len(words & _HIGH_TENSION_KEYWORDS)
    raw = 0.5 + (high * 0.15) - (low * 0.12)
    return _clamp(raw, 0.0, 1.0)


def _intent_to_focus(intent: str) -> float:
    lower = intent.lower()
    if any(k in lower for k in _FOCUS_INTENTS):
        return 80.0
    if any(k in lower for k in _OBSERVE_INTENTS):
        return 35.0
    return 60.0


def _derive_mood(
    energy: float, tension: float, focus: float, valence: float
) -> Literal["calm", "focused", "intense", "happy"]:
    if valence > 0.62 and energy > 65 and tension < 55:
        return "happy"
    if energy > 75 or tension > 72:
        return "intense"
    # Keep low-energy scenes calm even when the shot intent is narratively focused.
    if focus > 68 and energy >= 40:
        return "focused"
    return "calm"


def _derive_bpm(energy: float, focus: float, tension: float, valence: float) -> int:
    raw = 78 + energy * 0.72 + focus * 0.22 - tension * 0.2 + valence * 10
    return int(_clamp(raw, 70, 175))


def scene_state_from_shot(shot: Any) -> SceneState:
    """
    Build a SceneState from a TemporalShot dataclass or dict.
    Works with both Story Forge dataclasses and plain dicts.
    """
    if isinstance(shot, dict):
        pacing = shot.get("pacing", "medium")
        visual_intent = shot.get("visual_intent", "")
        intent = shot.get("intent", "")
        shot_number = shot.get("shot_number", 0)
        description = shot.get("description", "")
        duration_seconds = float(shot.get("duration_seconds", 3.0))
    else:
        pacing = getattr(shot, "pacing", "medium")
        visual_intent = getattr(shot, "visual_intent", "")
        intent = getattr(shot, "intent", "")
        shot_number = getattr(shot, "shot_number", 0)
        description = getattr(shot, "description", "")
        duration_seconds = float(getattr(shot, "duration_seconds", 3.0))

    energy = _pacing_to_energy(pacing)
    tension = _visual_intent_to_tension(visual_intent)
    valence = _visual_intent_to_valence(visual_intent)
    focus = _intent_to_focus(intent)

    mood = _derive_mood(energy, tension, focus, valence)
    bpm = _derive_bpm(energy, focus, tension, valence)

    return SceneState(
        energy=energy,
        tension=tension,
        focus=focus,
        valence=valence,
        mood=mood,
        bpm=bpm,
        shot_number=shot_number,
        description=description,
        intent=intent,
    )


def build_score_request_from_shot_list(
    shots: list[Any],
    session_id: str,
    scene_id: str,
    tone: str = "dark_fantasy",
    target: str = "movie",
    output_path: str = "",
) -> ScoreRequest:
    """
    Build a ScoreRequest from a list of TemporalShot objects or dicts.
    Computes cue start times from shot durations.
    """
    shot_states: list[ShotSceneState] = []
    cursor = 0.0

    for shot in shots:
        duration = float(
            shot.get("duration_seconds", 3.0)
            if isinstance(shot, dict)
            else getattr(shot, "duration_seconds", 3.0)
        )
        scene_state = scene_state_from_shot(shot)
        shot_states.append(ShotSceneState(
            shot_number=scene_state.shot_number,
            scene_state=scene_state,
            duration_seconds=duration,
            cue_start_seconds=cursor,
        ))
        cursor += duration

    return ScoreRequest(
        session_id=session_id,
        scene_id=scene_id,
        shots=shot_states,
        tone=tone,
        target=target,  # type: ignore[arg-type]
        output_path=output_path,
    )


def build_score_request_from_artifact(artifact: Any) -> ScoreRequest:
    """
    Convenience wrapper: build a ScoreRequest from a BackendBuildArtifact.
    Works with the real Story Forge artifact or a duck-typed object.
    """
    pkg = artifact.export_package
    session_id = getattr(artifact, "build_id", "unknown")
    scene_id = pkg.scene_id
    tone = pkg.metadata.get("tone", "dark_fantasy")
    target = pkg.metadata.get("target", "movie")

    # Prefer the full TemporalShot objects if available
    if hasattr(artifact, "temporal_shot_list"):
        shots = artifact.temporal_shot_list.shots
    else:
        # Fall back to locked_sequence dicts from final sequence
        shots = artifact.final_sequence.locked_sequence

    return build_score_request_from_shot_list(
        shots=shots,
        session_id=session_id,
        scene_id=scene_id,
        tone=tone,
        target=target,
    )
