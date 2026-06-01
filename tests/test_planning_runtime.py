"""Tests for Planning Runtime v1.3."""

import unittest

from src.cog_runtime.planning import (
    PLANNING_RUNTIME_ID,
    PLANNING_RUNTIME_VERSION,
    planning_runtime_spec,
    run_planning_turn,
    should_activate_planning,
    validate_planning_artifact,
)


class TestPlanningRuntime(unittest.TestCase):
    def test_spec_lists_stages(self):
        spec = planning_runtime_spec()
        self.assertEqual(spec["id"], PLANNING_RUNTIME_ID)
        self.assertEqual(spec["version"], "1.3")

    def test_run_planning_from_reflection(self):
        artifact, session = run_planning_turn(
            user_message="Should I pick A or B?",
            frame_kind="decision",
            reflection_artifact={
                "expected_outcome": "Deliver decision-aware answer",
                "alignment": "partial",
                "gaps": ["focus_not_reflected_in_delivery"],
                "adjustments": ["Surface primary focus earlier in the reply."],
                "next_turn_hints": ["Watch secondary focus: option B"],
                "planning_handoff": True,
            },
            focus_artifact={
                "primary_focus": "option A or B",
                "secondary_focus": ["option B"],
                "focus_signals": ["option A or B"],
                "weights": {},
                "salience": {},
                "signal_sources": {},
                "frame_kind": "decision",
                "suppressed": [],
            },
            cognitive_arc={"arc_id": "arc-1", "arc_turn_count": 2, "arc_goal": "choose option"},
        )
        validation = validate_planning_artifact(artifact)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertTrue(artifact.get("execution_handoff"))
        self.assertTrue(artifact["steps"])
        self.assertTrue(artifact["next_action"])
        self.assertTrue(artifact.get("step_chains"))
        self.assertTrue(artifact.get("active_chain_id"))
        self.assertIsInstance(artifact.get("chain_scores"), dict)
        self.assertTrue(artifact.get("chain_selection_reason"))
        self.assertTrue(session.validate_turn()["valid"])

    def test_should_activate_on_companion_turn(self):
        self.assertTrue(should_activate_planning({}, companion_turn=True))


if __name__ == "__main__":
    unittest.main()
