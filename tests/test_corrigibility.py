"""Tests for AAIS-native corrigibility behavior."""

import unittest

from src.conversation_memory import ConversationSession
from src.corrigibility import corrigibility_engine


class TestCorrigibilityEngine(unittest.TestCase):
    """Verify explicit corrections map cleanly onto AAIS session state."""

    def test_fix_code_request_does_not_misfire_as_self_correction(self):
        """Normal coding requests should not be mistaken for Jarvis self-correction."""
        self.assertIsNone(
            corrigibility_engine.classify("Fix this route in api.py and tell me why it breaks.")
        )

    def test_self_correction_queues_pending_guidance(self):
        """Explicit operator corrections should be queued for the next generated reply."""
        session = ConversationSession("corr-1", system_prompt="You are Jarvis.")

        result = corrigibility_engine.handle_user_correction(
            session,
            "You're wrong, keep the answer local-first and private.",
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["tool_result"]["type"], "corrigibility")
        self.assertEqual(result["tool_result"]["status"], "queued")
        self.assertEqual(session.metadata["corrigibility"]["status"], "pending")
        self.assertEqual(session.metadata["corrigibility"]["pending"]["severity"], "strong")
        self.assertIn(
            "local-first and private",
            session.metadata["corrigibility"]["pending"]["guidance"].lower(),
        )

    def test_pending_correction_is_folded_into_next_generation_then_cleared(self):
        """Queued corrections should appear in the next prompt and clear after use."""
        session = ConversationSession("corr-2", system_prompt="You are Jarvis.")
        corrigibility_engine.handle_user_correction(
            session,
            "Correct yourself: stay focused on local-only deployment.",
        )

        prompt = corrigibility_engine.apply_to_next_generation(session)
        self.assertIsNotNone(prompt)
        self.assertIn("operator explicitly corrected", prompt.lower())

        messages = session.build_messages()
        self.assertIn(
            "operator explicitly corrected",
            messages[0]["content"].lower(),
        )

        corrigibility_engine.mark_generation_applied(session)
        self.assertIsNone(session.metadata["corrigibility"]["pending"])
        self.assertIsNone(session.metadata["corrigibility_prompt_block"])

    def test_rewind_skips_corrigibility_ack_and_removes_last_real_answer(self):
        """Session rewind should skip correction ack turns and remove the last substantive assistant reply."""
        session = ConversationSession("corr-3", system_prompt="You are Jarvis.")
        session.add_turn("user", "Give me the first answer.")
        session.add_turn("assistant", "First real answer.")
        session.add_turn(
            "assistant",
            "Correction acknowledged.",
            metadata={"tool_result": {"type": "corrigibility"}},
        )

        removed = session.rollback_last_assistant_turn(skip_tool_types={"corrigibility"})

        self.assertIsNotNone(removed)
        self.assertEqual(removed["content"], "First real answer.")
        remaining_assistant_turns = [turn.content for turn in session.turns if turn.role == "assistant"]
        self.assertEqual(remaining_assistant_turns, ["Correction acknowledged."])


if __name__ == "__main__":
    unittest.main()
