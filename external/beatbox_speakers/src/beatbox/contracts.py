"""
Beatbox — Core Contracts
All data contracts for both score mode and live mode.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


# ── Scene State ──────────────────────────────────────────────────────────────

@dataclass
class SceneState:
    """
    Derived from TemporalShot fields.
    Replaces UserState from adaptive-music-v4.
    Primary driver for both score and live modes.
    """
    energy: float          # 0–100
    tension: float         # 0–100  (maps to "stress" in music engine)
    focus: float           # 0–100
    valence: float         # 0.0–1.0
    mood: Literal["calm", "focused", "intense", "happy"]
    bpm: int               # 70–175
    shot_number: int = 0
    description: str = ""
    intent: str = ""


@dataclass
class ShotSceneState:
    """One shot's scene state + its temporal position in the score."""
    shot_number: int
    scene_state: SceneState
    duration_seconds: float
    cue_start_seconds: float = 0.0   # filled in by score lane


# ── Score Mode Contracts ──────────────────────────────────────────────────────

@dataclass
class ScoreRequest:
    """Input to score mode. Derived from Story Forge BackendBuildArtifact."""
    session_id: str
    scene_id: str
    shots: list[ShotSceneState]
    tone: str = "dark_fantasy"
    target: Literal["movie", "game"] = "movie"
    output_path: str = ""


@dataclass
class MusicCue:
    """One music cue in the scored timeline."""
    shot_number: int
    cue_start_seconds: float
    duration_seconds: float
    mood: str
    bpm: int
    energy: float
    tension: float
    valence: float
    description: str = ""


@dataclass
class BeatboxArtifact:
    """Output of score mode. Handed to Speaker."""
    session_id: str
    scene_id: str
    audio_path: str
    timeline_path: str
    mode: Literal["score", "live"]
    provider: str
    continuity_passed: bool
    cue_count: int
    total_duration_seconds: float = 0.0
    cues: list[MusicCue] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "scene_id": self.scene_id,
            "audio_path": self.audio_path,
            "timeline_path": self.timeline_path,
            "mode": self.mode,
            "provider": self.provider,
            "continuity_passed": self.continuity_passed,
            "cue_count": self.cue_count,
            "total_duration_seconds": self.total_duration_seconds,
        }


# ── Live Mode Contracts ───────────────────────────────────────────────────────

@dataclass
class LiveStateUpdate:
    """Input to live mode. Driven by game state + optional player signal."""
    game_state: dict[str, Any]
    scene_emotion: str = "neutral"
    player_input_energy: float = 50.0    # from mic/sensor or manual
    player_input_stress: float = 35.0
    player_input_focus: float = 60.0
    intensity: float = 50.0              # 0–100 overall game intensity


# ── AAIS Boundary Result ──────────────────────────────────────────────────────

@dataclass
class BeatboxResult:
    """
    Deterministic result object.
    No raw exceptions cross this boundary.
    """
    ok: bool
    module: str = "beatbox"
    mode: Literal["score", "live"] = "score"
    data: Optional[BeatboxArtifact] = None
    error_type: Optional[str] = None
    message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, artifact: BeatboxArtifact, mode: str = "score") -> BeatboxResult:
        return cls(ok=True, mode=mode, data=artifact)  # type: ignore[arg-type]

    @classmethod
    def failure(cls, error_type: str, message: str,
                details: Optional[dict] = None, mode: str = "score") -> BeatboxResult:
        return cls(
            ok=False, mode=mode,  # type: ignore[arg-type]
            error_type=error_type,
            message=message,
            details=details or {},
        )
