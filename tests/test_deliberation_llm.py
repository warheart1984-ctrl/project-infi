"""Tests for LLM-assisted deliberation."""

import unittest

from src.cog_runtime.deliberation import run_deliberation_turn, validate_decision_object
from src.cog_runtime.deliberation_llm import (
    build_deliberation_prompt,
    parse_deliberation_response,
    run_deliberation_llm,
)


class TestDeliberationLlm(unittest.TestCase):
    def test_build_deliberation_prompt_includes_focus(self):
        prompt = build_deliberation_prompt(
            "Should I pick A or B?",
            focus_artifact={"primary_focus": "pick A or B", "focus_signals": ["pick A or B"]},
            frame_kind="decision",
        )
        self.assertIn("Primary focus", prompt["user"])
        self.assertIn("pick A or B", prompt["user"])

    def test_parse_deliberation_response_valid_json(self):
        payload = parse_deliberation_response(
            '{"options":["A","B"],"tradeoffs":[],"chosen_option":"A",'
            '"rationale":"A is simpler","assumptions":["stable goal"]}'
        )
        self.assertEqual(payload["chosen_option"], "A")

    def test_mock_deliberate_fn_used_on_turn(self):
        def mock_fn(prompt):
            return {
                "options": ["Skill", "Python module"],
                "tradeoffs": [],
                "chosen_option": "Python module",
                "rationale": "Better for repo integration.",
                "assumptions": ["Team prefers code artifacts"],
                "commit_source": "llm",
            }

        decision, session = run_deliberation_turn(
            "Should I use a skill or a Python module?",
            focus_artifact={"primary_focus": "Python module", "focus_signals": ["Python module"]},
            deliberate_fn=mock_fn,
            use_llm=True,
        )
        self.assertEqual(decision["commit_source"], "llm")
        self.assertEqual(decision["chosen_option"], "Python module")
        validation = validate_decision_object(decision)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertTrue(session.validate_turn()["valid"])

    def test_invalid_llm_falls_back_to_deterministic(self):
        def bad_fn(prompt):
            return None

        decision, _ = run_deliberation_turn(
            "Should I use Redis or Postgres?",
            focus_artifact={"primary_focus": "Redis or Postgres", "focus_signals": ["Redis"]},
            deliberate_fn=bad_fn,
            use_llm=True,
        )
        self.assertEqual(decision["commit_source"], "deterministic")
        self.assertTrue(decision["chosen_option"])

    def test_run_deliberation_llm_with_mock(self):
        def mock_fn(prompt):
            return parse_deliberation_response(
                '{"options":["X","Y"],"tradeoffs":[],"chosen_option":"X",'
                '"rationale":"test","assumptions":[]}'
            )

        result = run_deliberation_llm({"system": "s", "user": "u"}, deliberate_fn=mock_fn)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["chosen_option"], "X")


if __name__ == "__main__":
    unittest.main()
