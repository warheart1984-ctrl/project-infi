"""Tests for output completion integrity guards."""

import unittest

from src.output_completion import REPETITION_NOTICE, TRUNCATION_NOTICE, guard_output_completion


class TestOutputCompletion(unittest.TestCase):
    """Verify clipped replies are finalized cleanly or fail visibly."""

    def test_guard_adds_visible_notice_when_budget_stop_leaves_a_dangling_fragment(self):
        text, report = guard_output_completion(
            "The seam sits between the evaluation model and",
            stop_reason="max_new_tokens",
            finish_reason="length",
            output_token_budget=48,
            output_tokens_used=48,
        )

        self.assertNotIn("evaluation model and", text)
        self.assertIn(TRUNCATION_NOTICE, text)
        self.assertTrue(text.endswith(TRUNCATION_NOTICE))
        self.assertTrue(report.completion_guard_applied)
        self.assertTrue(report.visible_truncation_notice)
        self.assertEqual(report.structural_completion_status, "tail_trimmed_with_notice")

    def test_guard_keeps_complete_reply_unchanged_under_normal_budget(self):
        text, report = guard_output_completion(
            "The boundary is between prompt sizing and output finalization.",
            stop_reason="eos_token",
            finish_reason="stop",
            output_token_budget=128,
            output_tokens_used=22,
        )

        self.assertEqual(
            text,
            "The boundary is between prompt sizing and output finalization.",
        )
        self.assertFalse(report.completion_guard_applied)
        self.assertFalse(report.visible_truncation_notice)
        self.assertEqual(report.structural_completion_status, "complete")

    def test_guard_keeps_complete_reply_unchanged_under_budget_stop(self):
        text, report = guard_output_completion(
            (
                "I'm Jarvis. Claude is the underlying model I'm running on "
                '(Claude 3.5 Sonnet, routed as "First Sister" in this system).\n\n'
                "When I answer you, I'm speaking as Jarvis, the operator-facing "
                "sovereign core of your local AAIS. Claude is the reasoning engine underneath."
            ),
            stop_reason="max_tokens",
            finish_reason="length",
            output_token_budget=128,
            output_tokens_used=128,
        )

        self.assertNotIn(TRUNCATION_NOTICE, text)
        self.assertFalse(report.completion_guard_applied)
        self.assertFalse(report.visible_truncation_notice)
        self.assertFalse(report.truncation_detected)
        self.assertEqual(report.structural_completion_status, "complete_under_budget_pressure")

    def test_guard_does_not_infer_budget_pressure_from_estimated_usage_alone(self):
        text, report = guard_output_completion(
            "It sounds like you want reassurance before moving. Start with the single point you most need clarity on.",
            output_token_budget=30,
        )

        self.assertEqual(
            text,
            "It sounds like you want reassurance before moving. Start with the single point you most need clarity on.",
        )
        self.assertFalse(report.completion_guard_applied)
        self.assertFalse(report.truncation_detected)
        self.assertEqual(report.structural_completion_status, "complete")
        self.assertTrue(report.output_tokens_estimated)

    def test_guard_closes_unfinished_code_fence_with_visible_notice(self):
        text, report = guard_output_completion(
            "Plan:\n```python\nprint('repair seam')\n",
            stop_reason="max_new_tokens",
            finish_reason="length",
            output_token_budget=64,
            output_tokens_used=64,
        )

        self.assertNotIn("```python", text)
        self.assertIn(TRUNCATION_NOTICE, text)
        self.assertTrue(report.completion_guard_applied)
        self.assertIn("unclosed_code_fence", report.reasons)

    def test_guard_cuts_repeated_token_sequence_and_marks_repetition_notice(self):
        text, report = guard_output_completion(
            (
                "The fix is to add the completion guard once. "
                "add the completion guard once add the completion guard once "
                "add the completion guard once"
            ),
            stop_reason="eos_token",
            finish_reason="stop",
            output_token_budget=160,
            output_tokens_used=48,
        )

        self.assertIn(REPETITION_NOTICE, text)
        self.assertTrue(report.completion_guard_applied)
        self.assertTrue(report.repetition_detected)
        self.assertEqual(report.structural_completion_status, "repetition_loop_trimmed")
        self.assertIn("repeated_token_sequence", report.reasons)

    def test_guard_cuts_low_entropy_tail_even_without_budget_stop(self):
        text, report = guard_output_completion(
            (
                "The seam is at output finalization. "
                "steady steady steady steady steady steady steady steady steady steady "
                "steady steady steady steady steady steady"
            ),
            stop_reason="eos_token",
            finish_reason="stop",
            output_token_budget=200,
            output_tokens_used=40,
        )

        self.assertIn(REPETITION_NOTICE, text)
        self.assertTrue(report.repetition_detected)
        self.assertIn("low_entropy_tail", report.reasons)


if __name__ == "__main__":
    unittest.main()
