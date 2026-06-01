"""Governed AAIS capability entrypoints."""

from src.capabilities.story_forge_audio import (
    STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID,
    StoryForgeAudioCapability,
    authority_allows,
    ensure_story_forge_audio_capability_registered,
    ensure_story_forge_src,
    enforce_output_contract,
    run_story_forge_audio_capability,
    validate_request,
)

__all__ = [
    "STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID",
    "StoryForgeAudioCapability",
    "authority_allows",
    "ensure_story_forge_audio_capability_registered",
    "ensure_story_forge_src",
    "enforce_output_contract",
    "run_story_forge_audio_capability",
    "validate_request",
]
