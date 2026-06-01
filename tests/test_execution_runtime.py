"""Tests for Execution Runtime v1.1."""

import unittest

from src.cog_runtime.execution import (
    EXECUTION_RUNTIME_ID,
    EXECUTION_RUNTIME_VERSION,
    execution_runtime_spec,
    merge_post_reply_execution,
    run_execution_turn,
    should_activate_execution,
    validate_execution_artifact,
)


class TestExecutionRuntime(unittest.TestCase):
    def test_spec_lists_stages(self):
        spec = execution_runtime_spec()
        self.assertEqual(spec["id"], EXECUTION_RUNTIME_ID)
        self.assertEqual(spec["version"], "1.2")
        self.assertIn("recover", spec["stages"])
        self.assertIn("rollback", spec["stages"])

    def test_run_execution_turn_pre_reply(self):
        artifact, session = run_execution_turn(
            user_message="Should I pick A or B?",
            frame_kind="decision",
            planning_artifact={
                "arc_step": 1,
                "steps": ["Keep primary focus on: option A or B", "State chosen option clearly"],
                "checkpoints": ["Focus visible in opening lines"],
                "handoff_summary": "step 1",
                "next_action": "Keep primary focus on: option A or B",
                "execution_handoff": True,
            },
            focus_artifact={
                "primary_focus": "option A or B",
                "secondary_focus": [],
                "focus_signals": ["option A or B"],
                "weights": {},
                "salience": {},
                "signal_sources": {},
                "frame_kind": "decision",
                "suppressed": [],
            },
        )
        validation = validate_execution_artifact(artifact)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertEqual(artifact["verification_status"], "failed")
        self.assertFalse(artifact["recovered"])
        self.assertTrue(artifact["rollback_applied"])
        self.assertEqual(artifact["rollback_policy"], "applied_pre_reply")
        self.assertTrue(artifact.get("rollback_target"))
        self.assertTrue(artifact.get("recovery_paths"))
        self.assertGreaterEqual(artifact.get("recovery_tier", 0), 1)
        self.assertTrue(artifact.get("recovery_action"))
        self.assertTrue(session.validate_turn()["valid"])

    def test_merge_post_reply_execution_passes_when_aligned(self):
        planning = {
            "arc_step": 1,
            "steps": ["Recommend Postgres for durable cache"],
            "checkpoints": ["Focus visible in opening lines"],
            "handoff_summary": "step 1",
            "next_action": "Recommend Postgres for durable cache",
            "execution_handoff": True,
        }
        base, _ = run_execution_turn(
            planning_artifact=planning,
            focus_artifact={"primary_focus": "Postgres durable cache"},
        )
        merged = merge_post_reply_execution(
            base,
            speak_body="Focus: Postgres durable cache\n\nRecommend Postgres for durable cache because it fits your preference.",
            planning_artifact=planning,
            focus_artifact={"primary_focus": "Postgres durable cache"},
        )
        self.assertIn(merged["verification_status"], {"passed", "partial"})

    def test_should_activate_on_execution_handoff(self):
        self.assertTrue(
            should_activate_execution({"execution_handoff": True, "next_action": "Do X"})
        )


if __name__ == "__main__":
    unittest.main()
