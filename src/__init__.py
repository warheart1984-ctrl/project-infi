"""AAIS - AI Application"""

__version__ = "0.1.0"

from src.capabilities.story_forge_audio import (
    STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID,
    StoryForgeAudioCapability,
    run_story_forge_audio_capability,
)

__all__ = [
    "__version__",
    "STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID",
    "StoryForgeAudioCapability",
    "run_story_forge_audio_capability",
]
