"""Tests for the generic and runtime Jarvis provider registries."""

import os
import unittest
from unittest.mock import patch

from src.jarvis_provider_registry import ProviderConfig, ProviderRegistry
from src.provider_registry import ProviderRegistry as RuntimeProviderRegistry
from src.providers.local_provider import LocalProvider


class TestProviderRegistry(unittest.TestCase):
    """Verify provider selection rules stay simple and predictable."""

    def test_route_provider_prefers_explicit_request(self):
        """An explicit available provider should win over the default."""
        registry = ProviderRegistry()
        registry.register(
            ProviderConfig(name="gpt", display_name="OpenAI GPT", is_default=True),
            adapter="gpt-adapter",
        )
        registry.register(
            ProviderConfig(name="claude", display_name="Claude"),
            adapter="claude-adapter",
        )

        adapter, provider_name = registry.route_provider("claude")

        self.assertEqual(adapter, "claude-adapter")
        self.assertEqual(provider_name, "claude")

    def test_route_provider_falls_back_to_default(self):
        """When the requested provider is missing or disabled, the default should speak."""
        registry = ProviderRegistry()
        registry.register(
            ProviderConfig(name="gpt", display_name="OpenAI GPT", is_default=True),
            adapter="gpt-adapter",
        )
        registry.register(
            ProviderConfig(name="claude", display_name="Claude", enabled=False),
            adapter="claude-adapter",
        )

        adapter, provider_name = registry.route_provider("claude")

        self.assertEqual(adapter, "gpt-adapter")
        self.assertEqual(provider_name, "gpt")


class TestRuntimeProviderRegistry(unittest.TestCase):
    """Verify the AAIS runtime registry exposes compatibility helpers cleanly."""

    def test_get_provider_returns_local_adapter_by_default(self):
        """Runtime registry should expose the local provider as a protocol-capable adapter."""
        registry = RuntimeProviderRegistry()

        provider = registry.get_provider()

        self.assertIsInstance(provider, LocalProvider)

    def test_list_status_surfaces_activation_hint_for_missing_claude_key(self):
        """Offline Claude should expose the model and activation path instead of a raw count only."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "AAIS_CLAUDE_MODEL": "claude-test-model"}, clear=False):
            registry = RuntimeProviderRegistry()

        providers = {provider["id"]: provider for provider in registry.list_status()}

        self.assertEqual(providers["claude"]["model"], "claude-test-model")
        self.assertEqual(
            providers["claude"]["activation_hint"],
            "Add ANTHROPIC_API_KEY to .env to activate.",
        )

    def test_list_status_surfaces_openrouter_activation_hint_when_key_is_missing(self):
        """Offline OpenRouter should advertise the free-model activation path clearly."""
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "",
                "AAIS_OPENROUTER_MODEL": "openrouter/free",
            },
            clear=False,
        ):
            registry = RuntimeProviderRegistry()

        providers = {provider["id"]: provider for provider in registry.list_status()}

        self.assertEqual(providers["openrouter"]["model"], "openrouter/free")
        self.assertEqual(
            providers["openrouter"]["activation_hint"],
            "Add OPENROUTER_API_KEY to .env to activate free hosted models.",
        )

    def test_list_status_includes_frontier_catalog_entries(self):
        """Frontier adapters should appear in the provider list even when offline."""
        registry = RuntimeProviderRegistry()
        providers = {provider["id"]: provider for provider in registry.list_status()}
        self.assertIn("openai", providers)
        self.assertIn("google", providers)
        self.assertIn("nvidia", providers)
        self.assertIn("nemotron-3-nano", providers["nvidia"]["model"])
