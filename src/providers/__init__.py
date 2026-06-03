"""Provider adapters and compatibility exports for Jarvis-capable models."""

from src.providers.claude_provider import ClaudeProvider
from src.providers.frontier_catalog import FRONTIER_PROVIDER_SPECS, resolve_provider_alias
from src.providers.http_chat_provider import HttpChatProvider
from src.providers.local_provider import LocalProvider
from src.providers.openrouter_provider import OpenRouterProvider

__all__ = [
    "ClaudeProvider",
    "FRONTIER_PROVIDER_SPECS",
    "HttpChatProvider",
    "LocalProvider",
    "OpenRouterProvider",
    "resolve_provider_alias",
]
