"""Tests for Cortex v2.0 multi-turn cognitive arcs."""

import unittest
from types import SimpleNamespace

from src.cog_runtime.arcs import (
    ARC_RUNTIME_VERSION,
    CognitiveArc,
    GOAL_TYPES,
    append_arc_turn,
    infer_arc_goal_type,
    start_or_continue_arc,
    validate_cognitive_arc,
)
from src.cog_runtime.execution import EXECUTION_RUNTIME_ID
from src.cog_runtime.nova import configure_nova_cognitive_turn, run_nova_cognitive_turn
from src.cog_runtime.planning import PLANNING_RUNTIME_ID


class TestCortexArcs(unittest.TestCase):
    def test_arc_persists_across_companion_turns(self):
        session = SimpleNamespace(metadata={})
        configure_nova_cognitive_turn(
            session,
            {},
            "Should I take the fast path or the safe path?",
            companion_turn=True,
        )
        first_arc = dict(session.metadata.get("cortex_arc") or {})
        self.assertTrue(validate_cognitive_arc(first_arc)["valid"])
        self.assertEqual(first_arc.get("turn_count"), 1)
        self.assertIn(first_arc.get("goal_type"), GOAL_TYPES)

        configure_nova_cognitive_turn(
            session,
            {},
            "Let's continue with the safe path details",
            companion_turn=True,
        )
        second_arc = dict(session.metadata.get("cortex_arc") or {})
        self.assertEqual(second_arc.get("arc_id"), first_arc.get("arc_id"))
        self.assertEqual(second_arc.get("turn_count"), 2)
        self.assertGreaterEqual(len(second_arc.get("turns") or []), 2)

    def test_companion_turn_runs_reflection_planning_execution_loop(self):
        session = run_nova_cognitive_turn(
            "Should I pick option A or option B?",
            context={"companion_turn": True, "deliberation_llm": False},
        )
        self.assertIn("reflection_artifact", session.artifacts)
        self.assertIn("planning_artifact", session.artifacts)
        self.assertIn("execution_artifact", session.artifacts)
        self.assertIn(PLANNING_RUNTIME_ID, session.active_runtimes)
        self.assertIn(EXECUTION_RUNTIME_ID, session.active_runtimes)
        self.assertTrue(session.artifacts["planning_artifact"].get("execution_handoff"))

    def test_infer_arc_goal_type_decision(self):
        self.assertEqual(
            infer_arc_goal_type("Should I pick A or B?", frame_kind="decision"),
            "decision",
        )

    def test_goal_typed_arc_version(self):
        arc = CognitiveArc(goal="test", goal_type="continuity")
        payload = arc.to_dict()
        self.assertEqual(payload["goal_type"], "continuity")
        self.assertEqual(payload["arc_version"], ARC_RUNTIME_VERSION)
        self.assertIsInstance(payload.get("goal_hierarchy"), list)
        self.assertEqual(payload.get("goal_closure_status"), "open")
        self.assertIsInstance(payload.get("closed_subgoals"), list)
        self.assertTrue(validate_cognitive_arc(payload)["valid"])

    def test_append_arc_turn_records_next_action(self):
        arc = CognitiveArc(goal="test arc")
        cog_session = SimpleNamespace(
            session_id="s1",
            frame_kind="decision",
            artifacts={
                "focus_artifact": {"primary_focus": "pick cache"},
                "reflection_artifact": {"alignment": "aligned", "next_turn_hints": []},
                "planning_artifact": {"next_action": "Recommend Postgres"},
            },
        )
        updated = append_arc_turn(arc, user_message="Which cache?", cog_session=cog_session)
        self.assertEqual(updated.turn_count, 1)
        self.assertEqual(updated.turns[0]["next_action"], "Recommend Postgres")


if __name__ == "__main__":
    unittest.main()
