"""Assembler package for final video/audio muxing."""

from assembler.assemble_movie import assemble_movie, verify_ffmpeg
from assembler.contracts import AssemblyRequest

__all__ = ["AssemblyRequest", "assemble_movie", "verify_ffmpeg"]
