from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AssemblyRequest:
    session_id: str
    story_id: str
    run_id: str
    video_path: str
    audio_path: str
    output_path: str
    container: str = "mp4"
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    fps: int = 24
