from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Optional


if TYPE_CHECKING:
    from speakers.contracts import SpeakersMixPlan, VoiceProfile


@dataclass
class DialogueLine:
    shot_number: int
    character_id: str
    character_name: str
    text: str
    cue_start_seconds: float
    estimated_duration_seconds: float = 0.0


@dataclass
class NarrationLine:
    shot_number: int
    text: str
    cue_start_seconds: float
    estimated_duration_seconds: float = 0.0
    is_explicit: bool = True


@dataclass
class AudioPresentedOutput:
    session_id: str
    story_id: str
    run_id: str
    scene_id: str
    tone: str
    target: Literal["movie", "game"]
    shots: list[dict[str, Any]]
    dialogue_lines: list[DialogueLine] = field(default_factory=list)
    narration_lines: list[NarrationLine] = field(default_factory=list)
    voice_registry: dict[str, "VoiceProfile"] = field(default_factory=dict)
    narrator_profile: Optional["VoiceProfile"] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MusicCueEntry:
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
class BeatboxCuePlan:
    session_id: str
    story_id: str
    run_id: str
    scene_id: str
    tone: str
    target: Literal["movie", "game"]
    cues: list[MusicCueEntry] = field(default_factory=list)
    total_duration_seconds: float = 0.0

    def to_score_request(self, output_path: str = "") -> Any:
        from beatbox.contracts import SceneState, ScoreRequest, ShotSceneState

        shots = []
        for cue in self.cues:
            scene_state = SceneState(
                energy=cue.energy,
                tension=cue.tension,
                focus=60.0,
                valence=cue.valence,
                mood=cue.mood,  # type: ignore[arg-type]
                bpm=cue.bpm,
                shot_number=cue.shot_number,
                description=cue.description,
            )
            shots.append(
                ShotSceneState(
                    shot_number=cue.shot_number,
                    scene_state=scene_state,
                    duration_seconds=cue.duration_seconds,
                    cue_start_seconds=cue.cue_start_seconds,
                )
            )
        return ScoreRequest(
            session_id=self.session_id,
            scene_id=self.scene_id,
            shots=shots,
            tone=self.tone,
            target=self.target,
            output_path=output_path,
        )


@dataclass
class AudioPipelineResult:
    ok: bool
    session_id: str
    story_id: str
    run_id: str
    scene_id: str
    mix_plan: Optional["SpeakersMixPlan"] = None
    error_type: Optional[str] = None
    message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def success(
        cls,
        mix_plan: "SpeakersMixPlan",
        audit: Optional[list[dict[str, Any]]] = None,
    ) -> "AudioPipelineResult":
        return cls(
            ok=True,
            session_id=mix_plan.session_id,
            story_id=mix_plan.story_id,
            run_id=mix_plan.run_id,
            scene_id=mix_plan.scene_id,
            mix_plan=mix_plan,
            audit=audit or [],
        )

    @classmethod
    def failure(
        cls,
        session_id: str,
        story_id: str,
        run_id: str,
        scene_id: str,
        error_type: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> "AudioPipelineResult":
        return cls(
            ok=False,
            session_id=session_id,
            story_id=story_id,
            run_id=run_id,
            scene_id=scene_id,
            error_type=error_type,
            message=message,
            details=details or {},
        )


@dataclass
class FullPipelineRequest:
    presented_output: AudioPresentedOutput
    video_path: str
    movie_output_path: str = ""
    mix_version: str = "full-pipeline-v1"
    mix_filename_pattern: str = "{story_id}_{run_id}_final_mix.wav"
    mix_format: str = "wav"
    sample_rate: int = 44100
    bit_depth: int = 16
    channels: int = 1
    duck_amount_db: float = 8.0
    target_lufs: float = -16.0
    peak_ceiling_db: float = -1.0
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    fps: int = 24
    container: str = "mp4"


@dataclass
class FullPipelineResult:
    ok: bool
    session_id: str
    story_id: str
    run_id: str
    scene_id: str
    mix_plan: Optional["SpeakersMixPlan"] = None
    final_audio_path: str = ""
    movie_path: str = ""
    error_type: Optional[str] = None
    message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def success(
        cls,
        request: FullPipelineRequest,
        mix_plan: "SpeakersMixPlan",
        final_audio_path: str,
        movie_path: str,
        audit: Optional[list[dict[str, Any]]] = None,
    ) -> "FullPipelineResult":
        apo = request.presented_output
        return cls(
            ok=True,
            session_id=apo.session_id,
            story_id=apo.story_id,
            run_id=apo.run_id,
            scene_id=apo.scene_id,
            mix_plan=mix_plan,
            final_audio_path=final_audio_path,
            movie_path=movie_path,
            audit=audit or [],
        )

    @classmethod
    def failure(
        cls,
        request: FullPipelineRequest,
        error_type: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
        audit: Optional[list[dict[str, Any]]] = None,
        mix_plan: Optional["SpeakersMixPlan"] = None,
        final_audio_path: str = "",
        movie_path: str = "",
    ) -> "FullPipelineResult":
        apo = request.presented_output
        return cls(
            ok=False,
            session_id=apo.session_id,
            story_id=apo.story_id,
            run_id=apo.run_id,
            scene_id=apo.scene_id,
            mix_plan=mix_plan,
            final_audio_path=final_audio_path,
            movie_path=movie_path,
            error_type=error_type,
            message=message,
            details=details or {},
            audit=audit or [],
        )
