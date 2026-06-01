"""Tests for Deliberation Runtime v1.2."""

import unittest

from src.cog_runtime.deliberation import (
    DELIBERATION_CRITERIA,
    DELIBERATION_RUNTIME_VERSION,
    DELIBERATION_STAGES,
    deliberation_runtime_spec,
    run_deliberation_turn,
    should_activate_deliberation,
    validate_decision_object,
)


def _sample_focus(**overrides):
    artifact = {
        "primary_focus": "Defer until more constraints are known",
        "secondary_focus": [],
        "focus_signals": ["Defer until more constraints are known"],
        "weights": {"Defer until more constraints are known": 0.95},
        "salience": {"Defer until more constraints are known": 0.95},
        "signal_sources": {"Defer until more constraints are known": "message"},
        "frame_kind": "decision",
        "suppressed": [],
    }
    artifact.update(overrides)
    return artifact


class TestDeliberationRuntime(unittest.TestCase):
    def test_spec_lists_stages_v12(self):
        spec = deliberation_runtime_spec()
        self.assertEqual(spec["id"], "cognitive.deliberation")
        self.assertEqual(spec["version"], DELIBERATION_RUNTIME_VERSION)
        self.assertEqual(spec["version"], "1.2")
        self.assertEqual(list(spec["stages"]), list(DELIBERATION_STAGES))

    def test_should_activate_on_decision_frame(self):
        self.assertTrue(
            should_activate_deliberation("Should I use Redis or Postgres for cache?")
        )
        self.assertFalse(should_activate_deliberation("What is a speaking runtime?"))

    def test_run_deliberation_produces_decision_object(self):
        decision, session = run_deliberation_turn(
            "Should I use a skill or a Python module?"
        )
        validation = validate_decision_object(decision)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertEqual(decision["commit_source"], "deterministic")
        self.assertTrue(decision["chosen_option"])
        self.assertIsInstance(decision["alternatives"], list)
        self.assertTrue(decision["rationale"])
        self.assertIsInstance(decision["assumptions"], list)
        self.assertIsInstance(decision["tradeoffs"], list)
        self.assertIsInstance(decision["criteria_scores"], dict)
        self.assertIsInstance(decision["winning_criteria"], list)
        for criterion in DELIBERATION_CRITERIA:
            self.assertIn(
                criterion,
                next(iter(decision["criteria_scores"].values())),
            )

        turn_validation = session.validate_turn()
        self.assertTrue(turn_validation["valid"], msg=turn_validation["issues"])
        completed = turn_validation["completed_stages"]
        self.assertIn("options", completed)
        self.assertIn("tradeoffs", completed)
        self.assertIn("commit", completed)

    def test_focus_artifact_changes_deterministic_commit(self):
        decision, _ = run_deliberation_turn(
            "help me decide what to do next",
            focus_artifact=_sample_focus(),
            context={"policy_posture": "cautious"},
        )
        self.assertIn("Defer", decision["chosen_option"])

    def test_criteria_scores_change_with_focus(self):
        defer_focus = _sample_focus()
        action_focus = _sample_focus(
            primary_focus="Take the most direct actionable path",
            focus_signals=["Take the most direct actionable path"],
            weights={"Take the most direct actionable path": 0.95},
            salience={"Take the most direct actionable path": 0.95},
            signal_sources={"Take the most direct actionable path": "message"},
        )
        defer_decision, _ = run_deliberation_turn(
            "help me decide what to do next",
            focus_artifact=defer_focus,
            context={"policy_posture": "cautious"},
        )
        action_decision, _ = run_deliberation_turn(
            "help me decide what to do next",
            focus_artifact=action_focus,
            context={"policy_posture": "nominal"},
        )
        self.assertNotEqual(
            defer_decision["chosen_option"],
            action_decision["chosen_option"],
        )

    def test_revisit_stage_on_correction(self):
        _, session = run_deliberation_turn(
            "Should I pick A or B?",
            context={"user_correction": True},
        )
        completed = session.validate_turn()["completed_stages"]
        self.assertIn("revisit", completed)


if __name__ == "__main__":
    unittest.main()
