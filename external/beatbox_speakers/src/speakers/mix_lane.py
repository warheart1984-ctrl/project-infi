from __future__ import annotations

import contextlib
import math
import shutil
import struct
import subprocess
import tempfile
import wave
from array import array
from pathlib import Path
from typing import Dict, Iterable, List

from speakers.contracts import SpeakersMixPlan


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _resolve_ffmpeg() -> str | None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    try:
        import imageio_ffmpeg  # type: ignore[import]
    except ImportError:
        return None
    return imageio_ffmpeg.get_ffmpeg_exe()


def _read_wav_mono(path: str) -> tuple[int, array]:
    with wave.open(path, "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        framerate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())
    if sample_width != 2:
        raise ValueError(f"Expected 16-bit PCM WAV: {path}")
    samples = array("h")
    samples.frombytes(frames)
    if channels == 1:
        return framerate, samples
    if channels != 2:
        raise ValueError(f"Expected mono or stereo WAV: {path}")
    mono = array("h")
    for i in range(0, len(samples), 2):
        mono.append(int((samples[i] + samples[i + 1]) / 2))
    return framerate, mono


def _write_wav_mono(path: Path, sample_rate: int, samples: array) -> None:
    _ensure_dir(path)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples.tobytes())


def _concat_wav_files(paths: List[str], out_path: Path) -> Path:
    sample_rate = 44100
    combined = array("h")
    for path in paths:
        current_rate, samples = _read_wav_mono(path)
        if current_rate != sample_rate and combined:
            raise ValueError("All fallback WAV files must share a sample rate.")
        sample_rate = current_rate
        combined.extend(samples)
    _write_wav_mono(out_path, sample_rate, combined)
    return out_path


def _mix_wav_files(music_path: str | None, voice_path: str | None, out_path: Path, *, music_gain: float) -> Path:
    if not music_path and not voice_path:
        raise ValueError("No stems provided for mix")

    sample_rate = 44100
    music_samples = array("h")
    voice_samples = array("h")

    if music_path:
        sample_rate, music_samples = _read_wav_mono(music_path)
    if voice_path:
        voice_rate, voice_samples = _read_wav_mono(voice_path)
        if music_path and voice_rate != sample_rate:
            raise ValueError("Voice and music sample rates must match for WAV fallback.")
        sample_rate = voice_rate

    max_len = max(len(music_samples), len(voice_samples))
    mixed = array("h")
    for i in range(max_len):
        music_value = music_samples[i] if i < len(music_samples) else 0
        voice_value = voice_samples[i] if i < len(voice_samples) else 0
        sample = int(music_value * music_gain + voice_value)
        sample = max(-32768, min(32767, sample))
        mixed.append(sample)

    _write_wav_mono(out_path, sample_rate, mixed)
    return out_path


def _voice_duck_gain(mix_plan: SpeakersMixPlan) -> float:
    for rule in mix_plan.ducking_rules:
        if rule.when_source.lower() == "voice" and rule.affects.lower() == "music":
            amount = abs(rule.duck_amount_db)
            return math.pow(10, (-amount / 20.0))
    return 0.4


def _default_render_target_for_plan(mix_plan: SpeakersMixPlan) -> None:
    if mix_plan.render_targets:
        return
    from speakers.contracts import RenderTarget

    mix_plan.render_targets.append(
        RenderTarget(
            target_id="wav_master",
            format="wav",
            sample_rate=44100,
            bit_depth=16,
            channels=1,
            filename_pattern="{story_id}_{run_id}_final_mix.wav",
        )
    )


def render_final_mix(
    mix_plan: SpeakersMixPlan,
    voice_stems_manifest: Dict[str, str],
    music_stems_manifest: Dict[str, str],
    output_root: str,
) -> str:
    """
    v0 mix:
    - concatenates all voice stems in manifest order into one temporary voice track
    - uses the first music stem if present
    - applies fixed music ducking under voice
    - falls back to pure-Python WAV mixing when ffmpeg is unavailable
    """
    if not mix_plan.render_targets:
        raise ValueError("Mix plan must include at least one render target.")

    root = Path(output_root)
    target = mix_plan.render_targets[0]
    out_filename = target.filename_pattern.format(
        story_id=mix_plan.story_id,
        run_id=mix_plan.run_id,
    )
    out_path = root / mix_plan.session_id / "mix" / out_filename
    _ensure_dir(out_path)

    voice_files = list(voice_stems_manifest.values())
    music_files = list(music_stems_manifest.values())
    if not voice_files and mix_plan.voice_stem is not None:
        voice_files = [mix_plan.voice_stem.file_path]
    if not music_files and mix_plan.music_stem is not None:
        music_files = [mix_plan.music_stem.file_path]
    if not music_files and not voice_files:
        raise ValueError("No stems provided for mix")

    with tempfile.TemporaryDirectory(prefix="speakers_mix_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        voice_track: Path | None = None
        if voice_files:
            voice_track = _concat_wav_files(voice_files, tmp_root / "voice_track.wav")

        music_track = Path(music_files[0]) if music_files else None
        duck_gain = _voice_duck_gain(mix_plan)

        if target.format.lower() == "wav":
            result = _mix_wav_files(
                str(music_track) if music_track else None,
                str(voice_track) if voice_track else None,
                out_path,
                music_gain=duck_gain if voice_track and music_track else 1.0,
            )
            return str(result)

        ffmpeg = _resolve_ffmpeg()
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required for non-WAV render targets.")

        inputs: list[str] = []
        filters: list[str] = []
        idx = 0

        if music_track:
            inputs.extend(["-i", str(music_track)])
            filters.append(f"[{idx}:a]volume=1.0[a_music]")
            idx += 1
        if voice_track:
            inputs.extend(["-i", str(voice_track)])
            filters.append(f"[{idx}:a]volume=1.0[a_voice]")
            idx += 1

        if music_track and voice_track:
            filter_complex = (
                ";".join(filters)
                + f";[a_music]volume={duck_gain:.6f}[a_music_duck];"
                + "[a_music_duck][a_voice]amix=inputs=2:normalize=0[a_out]"
            )
            map_val = "[a_out]"
        elif music_track:
            filter_complex = ";".join(filters)
            map_val = "[a_music]"
        else:
            filter_complex = ";".join(filters)
            map_val = "[a_voice]"

        cmd = [
            ffmpeg,
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            map_val,
            "-ar",
            str(target.sample_rate),
            "-ac",
            str(target.channels),
            str(out_path),
        ]
        subprocess.run(cmd, check=True)
        return str(out_path)


def render_final_mix_from_plan(mix_plan: SpeakersMixPlan, output_root: str) -> str:
    _default_render_target_for_plan(mix_plan)
    return render_final_mix(
        mix_plan,
        voice_stems_manifest={},
        music_stems_manifest={},
        output_root=output_root,
    )
