"""AAIS runtime provider registry built on the generic Jarvis registry."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from src.jarvis_provider_registry import ProviderConfig, ProviderRegistry as BaseProviderRegistry
from src.logger import get_logger
from src.providers.claude_provider import ClaudeProvider
from src.providers.local_provider import LocalProvider
from src.providers.openrouter_provider import OpenRouterProvider

logger = get_logger(__name__)

load_dotenv()


DEFAULT_CLAUDE_MODEL = "claude-3-7-sonnet-20250219"
DEFAULT_OPENROUTER_MODEL = "openrouter/free"


class ProviderRegistry(BaseProviderRegistry):
    """Track which Jarvis providers are configured and actually available."""

    def __init__(self) -> None:
        super().__init__()
        self.refresh()

    def refresh(self) -> None:
        """Refresh provider availability from the current local environment."""
        self._providers = {}
        self._adapters = {}
        claude_model = os.getenv("AAIS_CLAUDE_MODEL", "").strip() or DEFAULT_CLAUDE_MODEL

        self.register(
            ProviderConfig(
                name="local",
                display_name="Local Heroine",
                is_default=True,
                enabled=True,
                supports_stream=True,
                meta={
                    "kind": "local",
                    "summary": "Primary on-laptop AAIS model path.",
                    "reason": "Built into AAIS.",
                    "model": "AAIS local runtime",
                    "activation_hint": "",
                },
            ),
            adapter=LocalProvider(),
        )

        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        openrouter_model = os.getenv("AAIS_OPENROUTER_MODEL", "").strip() or DEFAULT_OPENROUTER_MODEL
        if not openrouter_key:
            self.register(
                ProviderConfig(
                    name="openrouter",
                    display_name="OpenRouter — Free Relay",
                    enabled=False,
                    supports_stream=True,
                    meta={
                        "kind": "remote",
                        "summary": "Free or low-cost open models through OpenRouter's OpenAI-compatible API.",
                        "reason": "OPENROUTER_API_KEY is not set.",
                        "model": openrouter_model,
                        "activation_hint": "Add OPENROUTER_API_KEY to .env to activate free hosted models.",
                    },
                ),
                adapter=None,
            )
        else:
            try:
                openrouter_adapter = OpenRouterProvider(api_key=openrouter_key, model=openrouter_model)
                self.register(
                    ProviderConfig(
                        name="openrouter",
                        display_name="OpenRouter — Free Relay",
                        enabled=True,
                        supports_stream=True,
                        meta={
                            "kind": "remote",
                            "summary": "Free or low-cost open models through OpenRouter's OpenAI-compatible API.",
                            "reason": "OpenRouter provider is configured.",
                            "model": openrouter_adapter.model,
                            "activation_hint": "",
                        },
                    ),
                    adapter=openrouter_adapter,
                )
            except Exception as exc:  # pragma: no cover - depends on runtime config
                logger.warning(f"OpenRouter provider unavailable: {exc}")
                self.register(
                    ProviderConfig(
                        name="openrouter",
                        display_name="OpenRouter — Free Relay",
                        enabled=False,
                        supports_stream=True,
                        meta={
                            "kind": "remote",
                            "summary": "Free or low-cost open models through OpenRouter's OpenAI-compatible API.",
                            "reason": str(exc),
                            "model": openrouter_model,
                            "activation_hint": "Verify OPENROUTER_API_KEY and your OpenRouter free model choice to activate.",
                        },
                    ),
                    adapter=None,
                )

        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            self.register(
                ProviderConfig(
                    name="claude",
                    display_name="Claude — First Sister",
                    enabled=False,
                    supports_stream=True,
                    meta={
                        "kind": "remote",
                        "summary": "Calm, precise external sister model through Anthropic.",
                        "reason": "ANTHROPIC_API_KEY is not set.",
                        "model": claude_model,
                        "activation_hint": "Add ANTHROPIC_API_KEY to .env to activate.",
                    },
                ),
                adapter=None,
            )
        else:
            try:
                adapter = ClaudeProvider(api_key=api_key)
                self.register(
                    ProviderConfig(
                        name="claude",
                        display_name="Claude — First Sister",
                        enabled=True,
                        supports_stream=True,
                        meta={
                            "kind": "remote",
                            "summary": "Calm, precise external sister model through Anthropic.",
                            "reason": "Anthropic provider is configured.",
                            "model": adapter.model,
                            "activation_hint": "",
                        },
                    ),
                    adapter=adapter,
                )
            except Exception as exc:  # pragma: no cover - depends on optional SDK/env
                logger.warning(f"Claude provider unavailable: {exc}")
                self.register(
                    ProviderConfig(
                        name="claude",
                        display_name="Claude — First Sister",
                        enabled=False,
                        supports_stream=True,
                        meta={
                            "kind": "remote",
                            "summary": "Calm, precise external sister model through Anthropic.",
                            "reason": str(exc),
                            "model": claude_model,
                            "activation_hint": "Install the Anthropic SDK and verify ANTHROPIC_API_KEY to activate.",
                        },
                    ),
                    adapter=None,
                )

        from src.providers.registry_bootstrap import register_frontier_providers

        register_frontier_providers(self)

    def can_invoke(self, provider_id: str | None) -> bool:
        normalized = str(provider_id or "local").strip().lower()
        return self.is_available(normalized)

    def register_all(self) -> None:
        """Compatibility alias for registry bootstrap code from older provider drafts."""
        self.refresh()

    def get_provider(self, name: str = "local"):
        """Return the requested provider adapter, falling back to the local default."""
        adapter, _resolved = self.route_provider(name, fallback_name="local")
        return adapter

    def list_status(self) -> list[dict[str, Any]]:
        """List providers in a UI-friendly compatibility shape."""
        payload = []
        for provider_id, config in sorted(self.list_providers().items()):
            payload.append(
                {
                    "id": provider_id,
                    "name": config.name,
                    "label": config.display_name,
                    "display_name": config.display_name,
                    "available": bool(config.enabled),
                    "is_default": bool(config.is_default),
                    "supports_stream": bool(config.supports_stream),
                    "kind": config.meta.get("kind"),
                    "summary": config.meta.get("summary"),
                    "reason": config.meta.get("reason"),
                    "model": config.meta.get("model"),
                    "activation_hint": config.meta.get("activation_hint"),
                }
            )
        return payload


provider_registry = ProviderRegistry()
