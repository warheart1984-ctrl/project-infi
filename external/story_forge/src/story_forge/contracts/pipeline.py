from __future__ import annotations

from dataclasses import dataclass


STAGE_TRANSLATION = "translation"
STAGE_STAGING = "staging"
STAGE_DIRECTIONAL = "directional"
STAGE_PRESENTATION = "presentation"
STAGE_CINEMATIC = "cinematic"
STAGE_ENGINE_HANDOFF = "engine_handoff"

PIPELINE_ORDER = (
    STAGE_TRANSLATION,
    STAGE_STAGING,
    STAGE_DIRECTIONAL,
    STAGE_PRESENTATION,
    STAGE_CINEMATIC,
    STAGE_ENGINE_HANDOFF,
)

TARGET_MOVIE = "movie"
TARGET_GAME = "game"
TARGET_BOTH = "both"
ALLOWED_TARGETS = (TARGET_MOVIE, TARGET_GAME)

FORMAT_SCREENPLAY = "screenplay"
FORMAT_INTERACTIVE_SCRIPT = "interactive_script"

LUMEN_MODE_CINEMATIC = "cinematic"
LUMEN_MODE_INTERACTIVE = "interactive"


@dataclass(slots=True)
class PipelineRequest:
    raw_text: str
    title: str
    target: str
