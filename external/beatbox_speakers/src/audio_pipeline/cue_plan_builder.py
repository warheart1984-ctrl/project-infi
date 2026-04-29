from __future__ import annotations

from audio_pipeline.contracts import AudioPresentedOutput, BeatboxCuePlan, MusicCueEntry
from beatbox.scene_state_builder import scene_state_from_shot


def build_cue_plan(apo: AudioPresentedOutput) -> BeatboxCuePlan:
    cues: list[MusicCueEntry] = []
    cursor = 0.0

    for shot in apo.shots:
        scene_state = scene_state_from_shot(shot)
        duration = float(shot.get("duration_seconds", 3.0))
        cues.append(
            MusicCueEntry(
                shot_number=scene_state.shot_number,
                cue_start_seconds=cursor,
                duration_seconds=duration,
                mood=scene_state.mood,
                bpm=scene_state.bpm,
                energy=scene_state.energy,
                tension=scene_state.tension,
                valence=scene_state.valence,
                description=scene_state.description,
            )
        )
        cursor += duration

    return BeatboxCuePlan(
        session_id=apo.session_id,
        story_id=apo.story_id,
        run_id=apo.run_id,
        scene_id=apo.scene_id,
        tone=apo.tone,
        target=apo.target,
        cues=cues,
        total_duration_seconds=cursor,
    )
