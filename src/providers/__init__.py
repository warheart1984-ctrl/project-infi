"""Provider adapters and compatibility exports for Jarvis-capable models."""

from src.providers.claude_provider import ClaudeProvider
from src.providers.local_provider import LocalProvider
from src.providers.openai_compat_providers import GroqProvider, NvidiaProvider
from src.providers.openrouter_provider import OpenRouterProvider

__all__ = ["ClaudeProvider", "LocalProvider", "OpenRouterProvider", "GroqProvider", "NvidiaProvider"]
