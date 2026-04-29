from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


Pace = Literal["slow", "normal", "fast"]


@dataclass
class VoiceProfile:
    character_id: str
    voice_profile_id: str
    style: Literal["narration", "dialogue"]
    base_pitch_shift: float = 0.0
    base_rate: float = 1.0
    character_name: str = ""
    tone_hint: str = "neutral"
    narrator: bool = False


@dataclass
class VoiceLine:
    line_id: str
    scene_id: str
    character_id: str
    text: str
    intended_emotion: str
    pace: Pace
    start_offset_hint_seconds: float
    pause_after_seconds: float
    emphasis_tokens: List[str] = field(default_factory=list)
    shot_number: int = 0
    line_type: Literal["dialogue", "narration"] = "dialogue"
    estimated_duration_seconds: float = 0.0


@dataclass
class SpeakersVoicePlan:
    session_id: str
    story_id: str
    run_id: str
    voices: List[VoiceProfile] = field(default_factory=list)
    lines: List[VoiceLine] = field(default_factory=list)
    total_duration_seconds: float = 0.0


@dataclass
class BusConfig:
    target_lufs: float
    peak_ceiling_db: float


@dataclass
class DuckingRule:
    rule_id: str
    when_source: str
    affects: str
    duck_amount_db: float
    attack_ms: int
    release_ms: int


@dataclass
class SceneMixOverride:
    scene_id: str
    music_bus_gain_db: float = 0.0
    fx_bus_gain_db: float = 0.0


@dataclass
class RenderTarget:
    target_id: str
    format: str
    sample_rate: int
    bit_depth: int
    channels: int
    filename_pattern: str


@dataclass
class StemEntry:
    stem_type: Literal["music", "voice"]
    file_path: str
    duration_seconds: float
    provider: str


@dataclass
class TimingEntry:
    shot_number: int
    line_id: str
    stem_type: Literal["music", "voice"]
    cue_start_seconds: float
    duration_seconds: float
    voice_profile_id: str = ""
    text_preview: str = ""


@dataclass
class SpeakersMixPlan:
    session_id: str
    story_id: str
    run_id: str
    mix_version: str
    buses: Dict[str, BusConfig]
    scene_id: str = ""
    ducking_rules: List[DuckingRule] = field(default_factory=list)
    scene_mix_overrides: List[SceneMixOverride] = field(default_factory=list)
    render_targets: List[RenderTarget] = field(default_factory=list)
    music_stem: Optional[StemEntry] = None
    voice_stem: Optional[StemEntry] = None
    timing_map: List[TimingEntry] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    continuity_passed: bool = True
    issues: List[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "story_id": self.story_id,
            "run_id": self.run_id,
            "scene_id": self.scene_id,
            "mix_version": self.mix_version,
            "music_stem_path": self.music_stem.file_path if self.music_stem else None,
            "voice_stem_path": self.voice_stem.file_path if self.voice_stem else None,
            "total_duration_seconds": self.total_duration_seconds,
            "timing_entries": len(self.timing_map),
            "continuity_passed": self.continuity_passed,
            "issues": self.issues,
        }
