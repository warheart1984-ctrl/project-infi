"""Tests for the Mission Critic heuristics."""

import unittest

from src.critic import judge_pass, mission_critic


class TestMissionCritic(unittest.TestCase):
    """Ensure the critic scores mission movement in a stable way."""

    def test_review_reply_marks_actionable_mission_aligned_answer_as_advancing(self):
        review = mission_critic.review_reply(
            answer="Start by measuring cold-start latency again, then prewarm the model after boot.",
            user_message="Help me improve startup latency on this laptop.",
            mission_context={
                "active_mission": {
                    "title": "Stabilize startup latency",
                    "objective": "Improve startup latency on the local laptop runtime.",
                    "next_step": "Measure cold-start latency again.",
                    "blocker": None,
                    "tags": ["performance", "startup"],
                },
            },
            response_trace={"contract": "scope_build_ship", "plan_summary": "Focus: startup latency"},
            tool_result=None,
        )

        self.assertIsNotNone(review)
        self.assertEqual(review["source"], "reply")
        self.assertEqual(review["status"], "advancing")
        self.assertGreaterEqual(review["score"], 0.72)
        self.assertTrue(review["recommended_next"])

    def test_review_browser_verification_marks_failures_as_blocked(self):
        review = mission_critic.review_browser_verification(
            verification={
                "status": "fail",
                "target_path": "/settings",
                "suggested_action": {"id": "build_frontend", "label": "Build Frontend"},
                "route_expectation": {"fit": {"status": "mismatch"}},
                "next_steps": ["Inspect the settings page component and rebuild the frontend."],
            },
            mission_context={
                "active_mission": {
                    "title": "Fix Settings page",
                    "objective": "Fix the settings route and verify it against the live UI.",
                    "tags": ["browser", "route"],
                },
            },
        )

        self.assertIsNotNone(review)
        self.assertEqual(review["source"], "browser_verification")
        self.assertEqual(review["status"], "blocked")
        self.assertEqual(review["suggested_mission_status"], "blocked")
        self.assertIn("settings", review["summary"].lower())

    def test_judge_pass_compatibility_wrapper_preserves_old_shape(self):
        result = judge_pass(
            "Open api.py first, then verify the route with pytest.",
            "Debug the chat message route in api.py and verify it with tests.",
            "Help me debug the chat route.",
        )

        self.assertIn("score", result)
        self.assertIn("boost_needed", result)
        self.assertIn("issues", result)
        self.assertIn("summary", result)
        self.assertIsInstance(result["boost_needed"], bool)

