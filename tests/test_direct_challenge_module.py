"""Tests for the governed direct-challenge module."""

import unittest

from src.direct_challenge_module import (
    DirectChallengeModule,
    analyze_direct_challenge,
    build_adaptive_direct_challenge_anchor,
    classify_direct_challenge_intensity,
    stabilize_direct_challenge_reply,
)


class TestDirectChallengeModule(unittest.TestCase):
    """Verify severity, guidance, and adaptive anchors remain deterministic."""

    def test_classification_covers_low_medium_and_high(self):
        """Challenge intensity should remain explicit instead of binary-only."""
        self.assertEqual(classify_direct_challenge_intensity("seriously?"), "low")
        self.assertEqual(classify_direct_challenge_intensity("what is wrong with you?"), "medium")
        self.assertEqual(classify_direct_challenge_intensity("jarvis are you a moron?"), "high")
        self.assertEqual(classify_direct_challenge_intensity("summarize this file"), "none")

    def test_analysis_returns_anchor_guidance_and_markers(self):
        """Analysis should expose severity metadata for the runtime trace."""
        analysis = analyze_direct_challenge("jarvis are you useless?")

        self.assertTrue(analysis["detected"])
        self.assertEqual(analysis["severity"], "high")
        self.assertEqual(
            analysis["anchor_reply"],
            "No. If something is wrong, say it plainly and I'll deal with it.",
        )
        self.assertIn("worthlessness_claim", analysis["matched_markers"])
        self.assertIn("Stay calm and firm", analysis["guidance"])

    def test_stabilize_reply_uses_adaptive_anchor_when_identity_leaks(self):
        """Generic assistant leakage should collapse to the severity-aware anchor."""
        result = stabilize_direct_challenge_reply(
            "I'm an AI assistant. How can I assist you today?",
            user_input="what is wrong with you?",
        )

        self.assertTrue(result["identity_violation"])
        self.assertTrue(result["used_anchor"])
        self.assertEqual(
            result["final_text"],
            "No. If I missed something, point it out and I'll correct it.",
        )

    def test_clean_reply_survives_stabilization(self):
        """A clean Jarvis reply should not be replaced unnecessarily."""
        module = DirectChallengeModule()
        result = module.stabilize_reply(
            "No. Tell me what actually went wrong.",
            user_input="jarvis are you stupid?",
        )

        self.assertFalse(result["identity_violation"])
        self.assertFalse(result["used_anchor"])
        self.assertEqual(result["final_text"], "No. Tell me what actually went wrong.")
        self.assertEqual(build_adaptive_direct_challenge_anchor("low"), "No. But something didn't land. Tell me what felt off.")


if __name__ == "__main__":
    unittest.main()
