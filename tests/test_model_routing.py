"""Tests for turn-level provider-aware model routing."""

import unittest
from unittest.mock import patch

from src.model_routing import resolve_model_route


class TestModelRouting(unittest.TestCase):
    """Verify provider preferences and free-provider escalation stay predictable."""

    def test_manual_openrouter_preference_selects_remote_provider(self):
        route = resolve_model_route(
            response_mode="think",
            preferred_provider="openrouter",
            provider_available=lambda provider_id: provider_id in {"local", "openrouter"},
        )

        self.assertEqual(route["provider"], "openrouter")
        self.assertEqual(route["provider_kind"], "remote")
        self.assertEqual(route["provider_reason"], "manual_preference")
        self.assertEqual(route["provider_model"], "openrouter/free")

    def test_openrouter_auto_routing_can_escalate_research_turns(self):
        with patch.dict("os.environ", {"AAIS_ENABLE_OPENROUTER_AUTO_ROUTING": "1"}, clear=False):
            route = resolve_model_route(
                response_mode="research",
                research_sources=2,
                preferred_provider="local",
                provider_available=lambda provider_id: provider_id in {"local", "openrouter"},
            )

        self.assertEqual(route["provider"], "openrouter")
        self.assertEqual(route["provider_reason"], "auto_free_escalation")

    def test_auto_best_prefers_claude_for_reasoning_turns_when_available(self):
        route = resolve_model_route(
            response_mode="think",
            preferred_provider="auto",
            provider_available=lambda provider_id: provider_id in {"local", "claude"},
        )

        self.assertEqual(route["provider"], "claude")
        self.assertEqual(route["provider_reason"], "auto_best_reasoning")
        self.assertEqual(route["provider_kind"], "remote")

    def test_auto_best_uses_openrouter_when_claude_is_unavailable(self):
        route = resolve_model_route(
            response_mode="research",
            research_sources=2,
            preferred_provider="auto",
            provider_available=lambda provider_id: provider_id in {"local", "openrouter"},
        )

        self.assertEqual(route["provider"], "openrouter")
        self.assertEqual(route["provider_reason"], "auto_best_openrouter")

    def test_auto_best_keeps_debug_turns_local(self):
        route = resolve_model_route(
            response_mode="debug",
            preferred_provider="auto",
            provider_available=lambda provider_id: provider_id in {"local", "claude", "openrouter"},
        )

        self.assertEqual(route["provider"], "local")
        self.assertEqual(route["provider_reason"], "auto_best_local")

    def test_claude_hotwire_can_escalate_reasoning_turns_when_enabled(self):
        with patch.dict("os.environ", {"AAIS_ENABLE_CLAUDE_AUTO_ROUTING": "1"}, clear=False):
            route = resolve_model_route(
                response_mode="think",
                preferred_provider="local",
                provider_available=lambda provider_id: provider_id in {"local", "claude"},
            )

        self.assertEqual(route["provider"], "claude")
        self.assertEqual(route["provider_reason"], "auto_claude_hotwire")
        self.assertEqual(route["provider_kind"], "remote")

    def test_tiny_route_keeps_jarvis_as_authority_lane(self):
        route = resolve_model_route(
            response_mode="tiny",
            preferred_provider="local",
            provider_available=lambda provider_id: provider_id == "local",
        )

        self.assertEqual(route["id"], "tiny_companion")
        self.assertEqual(route["surface_identity"], "tiny_nova")
        self.assertEqual(route["authority_lane"], "jarvis")
        self.assertEqual(route["routing_authority"], "jarvis")
        self.assertFalse(route["surface_replaces_authority"])
        self.assertEqual(route["system_shape"], "organismic")

    def test_small_route_keeps_jarvis_as_authority_lane(self):
        route = resolve_model_route(
            response_mode="small",
            preferred_provider="local",
            provider_available=lambda provider_id: provider_id == "local",
        )

        self.assertEqual(route["id"], "small_companion")
        self.assertEqual(route["surface_identity"], "small_nova")
        self.assertEqual(route["authority_lane"], "jarvis")
        self.assertEqual(route["routing_authority"], "jarvis")
        self.assertFalse(route["surface_replaces_authority"])
        self.assertEqual(route["system_shape"], "organismic")

    def test_super_route_keeps_jarvis_as_authority_lane(self):
        route = resolve_model_route(
            response_mode="governed_full",
            preferred_provider="local",
            provider_available=lambda provider_id: provider_id == "local",
        )

        self.assertEqual(route["id"], "super_companion")
        self.assertEqual(route["surface_identity"], "super_nova")
        self.assertEqual(route["authority_lane"], "jarvis")
        self.assertEqual(route["routing_authority"], "jarvis")
        self.assertFalse(route["surface_replaces_authority"])
        self.assertEqual(route["system_shape"], "organismic")
