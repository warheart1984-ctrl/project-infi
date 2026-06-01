"""
Beatbox — Music Engine
Core music generation logic preserved from adaptive-music-v4,
adapted to accept SceneState instead of UserState.
No external dependencies required for deterministic output.
MIDI export requires midiutil (optional).
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Optional

from beatbox.contracts import MusicCue, SceneState, ShotSceneState


# ── Music Data ────────────────────────────────────────────────────────────────

CHORD_SETS: dict[str, list[list[str]]] = {
    "calm":    [["C4","E4","G4"], ["A3","C4","E4"], ["F3","A3","C4"], ["G3","B3","D4"]],
    "focused": [["D4","A4","C5"], ["Bb3","D4","F4"], ["F3","A3","C4"], ["C4","E4","G4"]],
    "intense": [["E3","G3","B3"], ["C3","Eb3","G3"], ["D3","F3","A3"], ["B2","D3","F#3"]],
    "happy":   [["C4","G4","A4"], ["F3","A3","C4"], ["G3","B3","D4"], ["E3","G3","C4"]],
}

BASS_ROOTS: dict[str, list[str]] = {
    "calm":    ["C2","A1","F1","G1"],
    "focused": ["D2","Bb1","F1","C2"],
    "intense": ["E1","C1","D1","B0"],
    "happy":   ["C2","F1","G1","E1"],
}

FALLBACK_VOCAL_PATTERNS: dict[str, list[dict[str, Any]]] = {
    "calm":    [{"note":"E4","durationBeats":1,"lyric":"breathe","velocity":0.55},
                {"note":"G4","durationBeats":1,"lyric":"slow","velocity":0.58},
                {"note":"A4","durationBeats":2,"lyric":"tonight","velocity":0.52},
                {"note":"G4","durationBeats":2,"lyric":"glow","velocity":0.5}],
    "focused": [{"note":"D4","durationBeats":1,"lyric":"lock","velocity":0.72},
                {"note":"F4","durationBeats":1,"lyric":"in","velocity":0.7},
                {"note":"A4","durationBeats":1,"lyric":"the","velocity":0.68},
                {"note":"C5","durationBeats":1,"lyric":"frame","velocity":0.74},
                {"note":"A4","durationBeats":2,"lyric":"steady","velocity":0.7}],
    "intense": [{"note":"E4","durationBeats":0.5,"lyric":"push","velocity":0.88},
                {"note":"G4","durationBeats":0.5,"lyric":"the","velocity":0.82},
                {"note":"B4","durationBeats":1,"lyric":"fire","velocity":0.9},
                {"note":"A4","durationBeats":1,"lyric":"higher","velocity":0.86},
                {"note":"G4","durationBeats":1,"lyric":"now","velocity":0.84}],
    "happy":   [{"note":"G4","durationBeats":1,"lyric":"rise","velocity":0.76},
                {"note":"A4","durationBeats":1,"lyric":"up","velocity":0.78},
                {"note":"C5","durationBeats":1,"lyric":"into","velocity":0.74},
                {"note":"A4","durationBeats":1,"lyric":"the","velocity":0.72},
                {"note":"G4","durationBeats":2,"lyric":"light","velocity":0.74}],
}

LYRIC_TEMPLATES: dict[str, list[str]] = {
    "calm":    ["Breathe slow, let the night move softly",
                "Every step turns quiet into light",
                "Hold the line, keep your center glowing"],
    "focused": ["Eyes ahead, every second is a signal",
                "Build the rhythm, lock into the frame",
                "Cut through noise, stay sharp inside the motion"],
    "intense": ["Heart up, fire in the circuit",
                "Push the pulse, break into the ceiling",
                "No delay, turn pressure into power"],
    "happy":   ["Sunrise in the speakers, lift it higher",
                "Bright feet on the floor, catch the feeling",
                "Laugh loud, let the chorus open wide"],
}


# ── Drum Patterns ─────────────────────────────────────────────────────────────

@dataclass
class DrumPattern:
    kick:  list[bool]
    snare: list[bool]
    hat:   list[bool]


def create_drum_pattern(mood: str, energy: float, focus: float, tension: float) -> DrumPattern:
    kick  = [False] * 16
    snare = [False] * 16
    hat   = [False] * 16

    for i in range(16):
        if i % 4 == 0:
            kick[i] = True
        if i in (4, 12):
            snare[i] = True

    if mood == "happy":
        for i in (0, 4, 8, 12, 2, 6, 10, 14):
            hat[i] = True
        if energy > 75:
            kick[10] = True

    elif mood == "focused":
        for i in range(0, 16, 2):
            hat[i] = True
        if focus > 75:
            hat[15] = True

    elif mood == "intense":
        for i in range(16):
            hat[i] = True
        for i in (3, 7, 11, 15):
            kick[i] = True
        if tension > 75 or energy > 80:
            snare[7] = True
            snare[15] = True

    elif mood == "calm":
        for i in (0, 4, 8, 12):
            hat[i] = True
        if tension < 30:
            hat[10] = True

    return DrumPattern(kick=kick, snare=snare, hat=hat)


# ── Arrangement ───────────────────────────────────────────────────────────────

@dataclass
class Arrangement:
    bars: int
    bpm: int
    ppq: int
    ticks_per_16: int
    drum_pattern: DrumPattern
    bass_roots: list[str]
    chords: list[list[str]]
    vocal_notes: list[dict[str, Any]]


def build_arrangement(state: SceneState, vocal_notes: Optional[list[dict[str, Any]]] = None) -> Arrangement:
    mood = state.mood
    bars = max(4, math.ceil(3.0 / (60.0 / max(state.bpm, 1)) / 4))  # ~3s minimum
    return Arrangement(
        bars=bars,
        bpm=state.bpm,
        ppq=480,
        ticks_per_16=120,
        drum_pattern=create_drum_pattern(mood, state.energy, state.focus, state.tension),
        bass_roots=BASS_ROOTS.get(mood, BASS_ROOTS["calm"]),
        chords=CHORD_SETS.get(mood, CHORD_SETS["calm"]),
        vocal_notes=vocal_notes if vocal_notes else FALLBACK_VOCAL_PATTERNS.get(mood, FALLBACK_VOCAL_PATTERNS["calm"]),
    )


def build_lyrics(mood: str, description: str, tone: str) -> list[str]:
    base = LYRIC_TEMPLATES.get(mood, LYRIC_TEMPLATES["calm"])
    return [
        base[0],
        f"Scene: {description[:40]}" if description else base[1],
        base[1],
        f"Tone: {tone.replace('_', ' ')}" if tone else base[2],
        base[2],
        "The score holds what words cannot",
    ]


# ── Cue Builder ───────────────────────────────────────────────────────────────

def build_cue_from_shot(shot_state: ShotSceneState) -> MusicCue:
    ss = shot_state.scene_state
    return MusicCue(
        shot_number=shot_state.shot_number,
        cue_start_seconds=shot_state.cue_start_seconds,
        duration_seconds=shot_state.duration_seconds,
        mood=ss.mood,
        bpm=ss.bpm,
        energy=ss.energy,
        tension=ss.tension,
        valence=ss.valence,
        description=ss.description,
    )


# ── MIDI Export ───────────────────────────────────────────────────────────────

def export_midi_bytes(state: SceneState, vocal_notes: Optional[list[dict[str, Any]]] = None) -> Optional[bytes]:
    """
    Export a MIDI arrangement for a single SceneState.
    Returns None if midiutil is not available.
    """
    try:
        from midiutil import MIDIFile  # type: ignore[import]
    except ImportError:
        return None

    arr = build_arrangement(state, vocal_notes)
    midi = MIDIFile(4)  # 4 tracks: drums, bass, chords, vocals

    for track, name in enumerate(["Drums", "Bass", "Chords", "Vocals"]):
        midi.addTrackName(track, 0, name)
        midi.addTempo(track, 0, arr.bpm)

    # Drums (track 0, channel 9)
    for bar in range(arr.bars):
        bar_start = bar * 4.0  # in beats
        for step in range(16):
            beat = bar_start + step * 0.25
            if arr.drum_pattern.kick[step]:
                midi.addNote(0, 9, 36, beat, 0.25, 115)
            if arr.drum_pattern.snare[step]:
                midi.addNote(0, 9, 38, beat, 0.25, 83)
            if arr.drum_pattern.hat[step]:
                midi.addNote(0, 9, 42, beat, 0.125, 45)

    # Bass (track 1, channel 0)
    for bar in range(arr.bars):
        root_note = arr.bass_roots[bar % len(arr.bass_roots)]
        midi_note = _note_to_midi(root_note)
        midi.addNote(1, 0, midi_note, bar * 4.0, 2.0, 90)

    # Chords (track 2, channel 1)
    for bar in range(arr.bars):
        chord = arr.chords[bar % len(arr.chords)]
        for note in chord:
            midi.addNote(2, 1, _note_to_midi(note), bar * 4.0, 4.0, 58)

    # Vocals (track 3, channel 2)
    cursor = 0.0
    while cursor < arr.bars * 4.0:
        for event in arr.vocal_notes:
            dur = max(0.25, float(event.get("durationBeats", 1)))
            vel = int(max(26, min(127, float(event.get("velocity", 0.7)) * 127)))
            midi.addNote(3, 2, _note_to_midi(event.get("note", "C4")), cursor, dur, vel)
            cursor += dur
            if cursor >= arr.bars * 4.0:
                break

    import io
    buf = io.BytesIO()
    midi.writeFile(buf)
    return buf.getvalue()


_NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
_ENHARMONICS = {"Bb": "A#", "Eb": "D#", "Ab": "G#", "Db": "C#", "Gb": "F#"}

def _note_to_midi(note: str) -> int:
    """Convert note string like 'C4', 'Bb3', 'F#3' to MIDI number."""
    if len(note) >= 2 and note[-1].isdigit():
        octave = int(note[-1])
        name = note[:-1]
    else:
        octave = 4
        name = note
    name = _ENHARMONICS.get(name, name)
    if name not in _NOTE_NAMES:
        return 60  # fallback to middle C
    return (_NOTE_NAMES.index(name)) + (octave + 1) * 12
