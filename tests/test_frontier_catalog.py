"""Tests for frontier provider catalog and registry bootstrap."""

import os
import unittest
from unittest.mock import patch

from src.provider_registry import ProviderRegistry
from src.providers.frontier_catalog import (
    FRONTIER_PROVIDER_SPECS,
    resolve_provider_alias,
)
from src.providers.registry_bootstrap import register_frontier_providers


class TestFrontierCatalog(unittest.TestCase):
    def test_catalog_includes_nvidia_nemotron(self):
        nvidia = next(spec for spec in FRONTIER_PROVIDER_SPECS if spec.name == "nvidia")
        self.assertIn("nemotron-3-nano", nvidia.default_model)
        self.assertIn("Nemotron", nvidia.display_name)

    def test_resolve_provider_alias(self):
        self.assertEqual(resolve_provider_alias("gemini"), "google")
        self.assertEqual(resolve_provider_alias("nemotron"), "nvidia")

    def test_register_frontier_providers_lists_nvidia_disabled_without_key(self):
        registry = ProviderRegistry.__new__(ProviderRegistry)
        registry._providers = {}
        registry._adapters = {}
        with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}, clear=False):
            register_frontier_providers(registry)
        nvidia = registry.get_config("nvidia")
        self.assertIsNotNone(nvidia)
        self.assertFalse(nvidia.enabled)
        self.assertIn("NVIDIA_API_KEY", nvidia.meta.get("activation_hint", ""))

    def test_register_frontier_providers_enables_nvidia_with_key(self):
        registry = ProviderRegistry.__new__(ProviderRegistry)
        registry._providers = {}
        registry._adapters = {}
        with patch.dict(
            os.environ,
            {
                "NVIDIA_API_KEY": "test-nvidia-key",
                "AAIS_NVIDIA_MODEL": "nvidia/nemotron-3-nano-30b-a3b",
            },
            clear=False,
        ):
            register_frontier_providers(registry)
        self.assertTrue(registry.is_available("nvidia"))
        self.assertIsNotNone(registry.get("nvidia"))
