from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LumenVoiceDoctrine:
    version: str = "2026.04"
    default_tense: str = "present"
    default_perspective: str = "third_person_limited"
    interactive_mode: str = "interactive"
    cinematic_mode: str = "cinematic"
    max_blank_breaks: int = 2
    prohibited_narrative_prefixes: tuple[str, ...] = (
        "[visual recall",
        "[visual artifact",
        "artifacts:",
        "hooks:",
        "context:",
        "continuity hook:",
        "system:",
        "engine:",
        "prompt:",
        "menu:",
    )


@dataclass(frozen=True, slots=True)
class LumenPersona:
    name: str = "LUMEN"
    allowed_capabilities: tuple[str, ...] = ("present_state",)
    doctrine: LumenVoiceDoctrine = LumenVoiceDoctrine()


LUMEN_PERSONA = LumenPersona()
LUMEN_DOCTRINE = LUMEN_PERSONA.doctrine


def lumen_can_perform(capability: str) -> bool:
    return capability in LUMEN_PERSONA.allowed_capabilities
