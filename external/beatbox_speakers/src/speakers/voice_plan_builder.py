from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from speakers.contracts import SpeakersVoicePlan, VoiceLine, VoiceProfile


if TYPE_CHECKING:
    from audio_pipeline.contracts import AudioPresentedOutput, DialogueLine, NarrationLine


_PACE_MAP = {
    "slow": "slow",
    "medium": "normal",
    "normal": "normal",
    "fast": "fast",
}


def _line_id(prefix: str, shot_number: int, idx: int) -> str:
    raw = f"{prefix}:{shot_number}:{idx}"
    return "line_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]


def _estimate_duration(text: str, base_rate: float = 1.0) -> float:
    words = len(text.split())
    return max(0.5, words / (2.3 * max(base_rate, 0.3)))


def _shot_pace(apo: "AudioPresentedOutput", shot_number: int) -> str:
    for shot in apo.shots:
        if int(shot.get("shot_number", 0)) == shot_number:
            return _PACE_MAP.get(str(shot.get("pacing", "medium")).lower(), "normal")
    return "normal"


def build_voice_plan(apo: "AudioPresentedOutput") -> SpeakersVoicePlan:
    voices: list[VoiceProfile] = list(apo.voice_registry.values())
    if apo.narrator_profile is not None:
        voices.append(apo.narrator_profile)

    lines: list[VoiceLine] = []
    total_duration = 0.0

    for idx, dialogue in enumerate(apo.dialogue_lines):
        profile = apo.voice_registry.get(dialogue.character_id)
        if profile is None:
            continue
        estimated = dialogue.estimated_duration_seconds or _estimate_duration(
            dialogue.text,
            base_rate=profile.base_rate,
        )
        line = VoiceLine(
            line_id=_line_id("dlg", dialogue.shot_number, idx),
            scene_id=apo.scene_id,
            character_id=dialogue.character_id,
            text=dialogue.text,
            intended_emotion=profile.tone_hint,
            pace=_shot_pace(apo, dialogue.shot_number),
            start_offset_hint_seconds=dialogue.cue_start_seconds,
            pause_after_seconds=0.2,
            emphasis_tokens=[],
            shot_number=dialogue.shot_number,
            line_type="dialogue",
            estimated_duration_seconds=estimated,
        )
        lines.append(line)
        total_duration = max(total_duration, line.start_offset_hint_seconds + estimated)

    if apo.narrator_profile is not None:
        for idx, narration in enumerate(apo.narration_lines):
            if not narration.is_explicit:
                continue
            estimated = narration.estimated_duration_seconds or _estimate_duration(
                narration.text,
                base_rate=apo.narrator_profile.base_rate,
            )
            line = VoiceLine(
                line_id=_line_id("nar", narration.shot_number, idx),
                scene_id=apo.scene_id,
                character_id=apo.narrator_profile.character_id,
                text=narration.text,
                intended_emotion=apo.narrator_profile.tone_hint,
                pace=_shot_pace(apo, narration.shot_number),
                start_offset_hint_seconds=narration.cue_start_seconds,
                pause_after_seconds=0.35,
                emphasis_tokens=[],
                shot_number=narration.shot_number,
                line_type="narration",
                estimated_duration_seconds=estimated,
            )
            lines.append(line)
            total_duration = max(total_duration, line.start_offset_hint_seconds + estimated)

    lines.sort(key=lambda item: (item.start_offset_hint_seconds, item.shot_number, item.line_id))
    return SpeakersVoicePlan(
        session_id=apo.session_id,
        story_id=apo.story_id,
        run_id=apo.run_id,
        voices=voices,
        lines=lines,
        total_duration_seconds=total_duration,
    )
