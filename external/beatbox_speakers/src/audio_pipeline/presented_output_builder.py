from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any, Iterable

from audio_pipeline.contracts import (
    AudioPresentedOutput,
    DialogueLine,
    NarrationLine,
)
from speakers.contracts import VoiceProfile


_VOICE_POOL = {
    "protagonist": "voice_lead_calm_01",
    "antagonist": "voice_antagonist_intense_01",
    "antagonist/lover": "voice_antagonist_intense_01",
    "supporting": "voice_support_warm_01",
    "participant": "voice_neutral_01",
    "narrator": "narrator_primary",
}
_TONE_POOL = {
    "voice_lead_calm_01": "calm",
    "voice_antagonist_intense_01": "intense",
    "voice_support_warm_01": "warm",
    "voice_neutral_01": "neutral",
    "narrator_primary": "calm",
}


def _profile_id_for_role(role: str) -> str:
    return _VOICE_POOL.get((role or "").lower().strip(), "voice_neutral_01")


def _stable_id(name: str) -> str:
    return "char_" + hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]


def _normalize_name(value: Any) -> str:
    return str(value or "").strip()


def _as_dicts(items: Iterable[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            rows.append(dict(item))
        else:
            rows.append(dict(vars(item)))
    return rows


def _find_character_id_by_name(
    registry: dict[str, VoiceProfile],
    character_name: str,
) -> str | None:
    target = character_name.upper()
    for character_id, profile in registry.items():
        if profile.character_name.upper() == target:
            return character_id
    return None


def _register_voice_profile(
    registry: dict[str, VoiceProfile],
    seen_profiles: dict[str, int],
    *,
    character_id: str,
    character_name: str,
    role: str,
) -> None:
    if character_id in registry:
        return

    voice_profile_id = _profile_id_for_role(role)
    if voice_profile_id in seen_profiles:
        seen_profiles[voice_profile_id] += 1
        voice_profile_id = f"{voice_profile_id}_{seen_profiles[voice_profile_id]}"
    else:
        seen_profiles[voice_profile_id] = 1

    registry[character_id] = VoiceProfile(
        character_id=character_id,
        character_name=character_name,
        voice_profile_id=voice_profile_id,
        style="dialogue",
        base_rate=1.0,
        tone_hint=_TONE_POOL.get(voice_profile_id.rsplit("_", 1)[0], _TONE_POOL.get(voice_profile_id, "neutral")),
    )


def build_voice_registry(
    entities: list[dict[str, Any]],
    dialogue_lines: list[dict[str, Any]] | None = None,
) -> dict[str, VoiceProfile]:
    registry: dict[str, VoiceProfile] = {}
    seen_profiles: dict[str, int] = {}

    for entity in entities:
        character_name = _normalize_name(entity.get("name", "Unknown")) or "Unknown"
        character_id = _normalize_name(entity.get("id")) or _stable_id(character_name)
        role = _normalize_name(entity.get("role", "participant")) or "participant"
        _register_voice_profile(
            registry,
            seen_profiles,
            character_id=character_id,
            character_name=character_name,
            role=role,
        )

    for line in dialogue_lines or []:
        character_name = _normalize_name(line.get("character_name"))
        if not character_name or character_name.upper() == "NARRATOR":
            continue
        character_id = _normalize_name(line.get("character_id"))
        if not character_id:
            character_id = _find_character_id_by_name(registry, character_name) or _stable_id(character_name)
        role = _normalize_name(line.get("role", "participant")) or "participant"
        _register_voice_profile(
            registry,
            seen_profiles,
            character_id=character_id,
            character_name=character_name,
            role=role,
        )

    return registry


def build_cue_timeline(shots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    cursor = 0.0
    for idx, shot in enumerate(shots):
        duration = float(shot.get("duration_seconds", 3.0))
        shot_number = int(shot.get("shot_number", idx + 1))
        timeline.append(
            {
                "shot_number": shot_number,
                "cue_start_seconds": cursor,
                "duration_seconds": duration,
            }
        )
        cursor += duration
    return timeline


def extract_dialogue_from_screenplay(
    screenplay: str,
    voice_registry: dict[str, VoiceProfile],
    cue_timeline: list[dict[str, Any]],
) -> list[DialogueLine]:
    name_to_id = {profile.character_name.upper(): character_id for character_id, profile in voice_registry.items()}
    cues = cue_timeline or [{"shot_number": 1, "cue_start_seconds": 0.0}]
    cue_index = 0
    dialogue_lines: list[DialogueLine] = []

    for raw_line in screenplay.splitlines():
        raw_line = raw_line.strip()
        if ":" not in raw_line:
            continue
        speaker_text, text = raw_line.split(":", 1)
        speaker = speaker_text.strip().upper()
        text = text.strip()
        if not text or speaker.startswith("SHOT") or speaker.startswith("FADE"):
            continue
        character_id = name_to_id.get(speaker)
        if character_id is None:
            continue
        cue = cues[min(cue_index, len(cues) - 1)]
        profile = voice_registry[character_id]
        dialogue_lines.append(
            DialogueLine(
                shot_number=int(cue.get("shot_number", cue_index + 1)),
                character_id=character_id,
                character_name=profile.character_name,
                text=text,
                cue_start_seconds=float(cue.get("cue_start_seconds", 0.0)),
            )
        )
        cue_index += 1
    return dialogue_lines


def build_dialogue_from_structured_lines(
    dialogue_lines: list[dict[str, Any]],
    voice_registry: dict[str, VoiceProfile],
    cue_timeline: list[dict[str, Any]],
) -> list[DialogueLine]:
    cues_by_shot = {
        int(cue.get("shot_number", index + 1)): cue
        for index, cue in enumerate(cue_timeline)
    }
    rows: list[DialogueLine] = []

    for index, raw_line in enumerate(dialogue_lines, start=1):
        text = _normalize_name(raw_line.get("text"))
        if not text:
            continue
        shot_number = int(raw_line.get("shot_number", index))
        character_id = _normalize_name(raw_line.get("character_id"))
        character_name = _normalize_name(raw_line.get("character_name"))

        if not character_id and character_name:
            character_id = _find_character_id_by_name(voice_registry, character_name) or _stable_id(character_name)
        profile = voice_registry.get(character_id)
        if profile is None and character_name:
            fallback_character_id = _find_character_id_by_name(voice_registry, character_name)
            if fallback_character_id is not None:
                character_id = fallback_character_id
                profile = voice_registry.get(character_id)
        if profile is None:
            continue

        cue = cues_by_shot.get(shot_number, {})
        cue_start_seconds = raw_line.get("cue_start_seconds")
        if cue_start_seconds in (None, ""):
            cue_start_seconds = cue.get("cue_start_seconds", 0.0)

        rows.append(
            DialogueLine(
                shot_number=shot_number,
                character_id=character_id,
                character_name=profile.character_name,
                text=text,
                cue_start_seconds=float(cue_start_seconds),
                estimated_duration_seconds=float(raw_line.get("estimated_duration_seconds", 0.0) or 0.0),
            )
        )

    rows.sort(key=lambda item: (item.cue_start_seconds, item.shot_number, item.character_name))
    return rows


def build_audio_presented_output(
    session_id: str,
    story_id: str,
    run_id: str,
    scene_id: str,
    shots: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    tone: str = "dark_fantasy",
    target: str = "movie",
    screenplay: str = "",
    dialogue_lines: list[dict[str, Any]] | None = None,
    narration_lines: list[dict[str, Any]] | None = None,
    cue_timeline: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AudioPresentedOutput:
    voice_registry = build_voice_registry(entities, dialogue_lines=dialogue_lines)
    timeline = cue_timeline or build_cue_timeline(shots)
    if dialogue_lines:
        dialogue = build_dialogue_from_structured_lines(dialogue_lines, voice_registry, timeline)
    else:
        dialogue = extract_dialogue_from_screenplay(screenplay, voice_registry, timeline)

    cues_by_shot = {
        int(cue.get("shot_number", index + 1)): cue
        for index, cue in enumerate(timeline)
    }

    narration: list[NarrationLine] = []
    for line in narration_lines or []:
        text = str(line.get("text", "")).strip()
        if not text:
            continue
        shot_number = int(line.get("shot_number", 0))
        cue = cues_by_shot.get(shot_number, {})
        cue_start_seconds = line.get("cue_start_seconds")
        if cue_start_seconds in (None, ""):
            cue_start_seconds = cue.get("cue_start_seconds", 0.0)
        narration.append(
            NarrationLine(
                shot_number=shot_number,
                text=text,
                cue_start_seconds=float(cue_start_seconds),
                estimated_duration_seconds=float(line.get("estimated_duration_seconds", 0.0) or 0.0),
                is_explicit=bool(line.get("is_explicit", True)),
            )
        )

    narrator_profile = None
    if narration:
        narrator_profile = VoiceProfile(
            character_id="NARRATOR",
            character_name="Narrator",
            voice_profile_id="narrator_primary",
            style="narration",
            base_rate=1.0,
            tone_hint="calm",
            narrator=True,
        )

    return AudioPresentedOutput(
        session_id=session_id,
        story_id=story_id,
        run_id=run_id,
        scene_id=scene_id,
        tone=tone,
        target=target,  # type: ignore[arg-type]
        shots=shots,
        dialogue_lines=dialogue,
        narration_lines=narration,
        voice_registry=voice_registry,
        narrator_profile=narrator_profile,
        metadata=deepcopy(metadata or {}),
    )


def build_audio_presented_output_from_artifact(artifact: Any) -> AudioPresentedOutput:
    export_package = artifact.export_package
    session_id = getattr(artifact, "session_id", getattr(artifact, "build_id", "unknown_session"))
    story_id = export_package.metadata.get("story_id", export_package.scene_id)
    run_id = export_package.metadata.get("run_id", session_id)
    scene_id = export_package.scene_id
    tone = export_package.metadata.get("tone", "dark_fantasy")
    target = export_package.metadata.get("target", "movie")

    if hasattr(artifact, "temporal_shot_list"):
        shots = _as_dicts(artifact.temporal_shot_list.shots)
    else:
        shots = _as_dicts(artifact.final_sequence.locked_sequence)

    if hasattr(artifact, "scene_object"):
        entities = _as_dicts(artifact.scene_object.entities)
    else:
        entities = []

    return build_audio_presented_output(
        session_id=session_id,
        story_id=story_id,
        run_id=run_id,
        scene_id=scene_id,
        shots=shots,
        entities=entities,
        tone=tone,
        target=target,
        screenplay=getattr(export_package, "screenplay", ""),
        dialogue_lines=export_package.metadata.get("dialogue_lines", []),
        narration_lines=export_package.metadata.get("narration_lines", []),
        metadata=dict(export_package.metadata),
    )
