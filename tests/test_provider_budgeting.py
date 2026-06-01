"""Tests for provider-aware prompt estimation and remote output budgeting."""

import unittest

from src.jarvis_protocol import JarvisMessage
from src.provider_budgeting import (
    estimate_provider_prompt_tokens,
    resolve_remote_output_budget,
)


class TestProviderBudgeting(unittest.TestCase):
    """Verify provider dispatch budgeting stays deterministic and bounded."""

    def test_resolve_remote_output_budget_clamps_when_prompt_estimate_overflows(self):
        messages = [
            JarvisMessage(role="system", content="support detail " * 120),
            JarvisMessage(role="user", content="evidence detail " * 120),
        ]

        report = resolve_remote_output_budget(
            provider_id="openrouter",
            provider_model="openrouter/free",
            messages=messages,
            requested_output_budget=192,
            prompt_token_budget=120,
            reply_budget_floor=160,
        )

        self.assertTrue(report["output_budget_clamped"])
        self.assertGreater(report["prompt_overflow_tokens"], 0)
        self.assertLess(report["effective_output_token_budget"], 192)
        self.assertEqual(report["prompt_tokens_estimator"], "openai_compatible_message_heuristic")

    def test_estimate_provider_prompt_tokens_handles_claude_system_messages(self):
        messages = [
            JarvisMessage(role="system", content="Stay grounded in local truth."),
            JarvisMessage(role="user", content="Help me inspect the runtime seam."),
            JarvisMessage(role="assistant", content="I will keep it bounded."),
        ]

        report = estimate_provider_prompt_tokens(
            "claude",
            messages,
            provider_model="claude-test",
        )

        self.assertEqual(report["provider"], "claude")
        self.assertEqual(report["provider_model"], "claude-test")
        self.assertEqual(report["estimator"], "anthropic_message_heuristic")
        self.assertEqual(report["system_message_count"], 1)
        self.assertGreater(report["prompt_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
