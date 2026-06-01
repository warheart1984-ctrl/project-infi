from __future__ import annotations

import importlib
import shutil
import subprocess
from pathlib import Path

from assembler.contracts import AssemblyRequest


def verify_ffmpeg() -> tuple[bool, str]:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return True, ffmpeg
    try:
        imageio_ffmpeg = importlib.import_module("imageio_ffmpeg")
    except ImportError:
        return False, ""
    return True, imageio_ffmpeg.get_ffmpeg_exe()


def _resolve_ffmpeg() -> str:
    available, ffmpeg = verify_ffmpeg()
    if available and ffmpeg:
        return ffmpeg
    raise RuntimeError("ffmpeg is required to assemble the final movie.")


def assemble_movie(req: AssemblyRequest) -> str:
    """
    Mux picture-only video + final audio into a single movie file.
    Assumes video_path has no usable final audio.
    """
    video = Path(req.video_path)
    audio = Path(req.audio_path)
    out = Path(req.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = _resolve_ffmpeg()
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-i",
        str(audio),
        "-c:v",
        req.video_codec,
        "-c:a",
        req.audio_codec,
        "-b:a",
        req.audio_bitrate,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-r",
        str(req.fps),
        str(out),
    ]

    subprocess.run(cmd, check=True)
    return str(out)
