"""Tests for Reflection Runtime v1.0."""

import unittest

from src.cog_runtime.reflection import (
    REFLECTION_RUNTIME_ID,
    REFLECTION_RUNTIME_VERSION,
    REFLECTION_STAGES,
    merge_post_reply_reflection,
    reflection_runtime_spec,
    run_reflection_turn,
    validate_reflection_artifact,
)


class TestReflectionRuntime(unittest.TestCase):
    def test_spec_lists_stages(self):
        spec = reflection_runtime_spec()
        self.assertEqual(spec["id"], REFLECTION_RUNTIME_ID)
        self.assertEqual(spec["version"], REFLECTION_RUNTIME_VERSION)
        self.assertEqual(REFLECTION_RUNTIME_VERSION, "1.3")
        self.assertEqual(list(spec["stages"]), list(REFLECTION_STAGES))

    def test_run_reflection_turn_pre_reply(self):
        artifact, session = run_reflection_turn(
            user_message="Should I use Redis or Postgres?",
            frame_kind="decision",
            focus_artifact={
                "primary_focus": "Redis or Postgres",
                "secondary_focus": [],
                "focus_signals": ["Redis or Postgres"],
                "weights": {"Redis or Postgres": 0.9},
                "salience": {"Redis or Postgres": 0.9},
                "signal_sources": {"Redis or Postgres": "message"},
                "frame_kind": "decision",
                "suppressed": [],
            },
            decision_object={
                "chosen_option": "Postgres",
                "alternatives": ["Redis"],
                "rationale": "Durability",
                "assumptions": [],
                "tradeoffs": [],
                "criteria_scores": {"Postgres": {"focus_alignment": 0.8}},
                "winning_criteria": ["focus_alignment"],
                "commit_source": "deterministic",
            },
            memory_artifact={
                "encoded": {"text": "cache preference"},
                "index_keys": ["postgres"],
                "retrieved_cues": ["Postgres durable cache preference"],
                "forgotten_advisory": [],
            },
        )
        validation = validate_reflection_artifact(artifact)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertIn(artifact["alignment"], {"aligned", "partial", "misaligned"})
        self.assertTrue(artifact.get("planning_handoff"))
        turn_validation = session.validate_turn()
        self.assertTrue(turn_validation["valid"], msg=turn_validation["issues"])
        self.assertEqual(turn_validation["completed_stages"], list(REFLECTION_STAGES))

    def test_merge_post_reply_reflection_detects_gap(self):
        base, _ = run_reflection_turn(
            user_message="Should I use Redis or Postgres?",
            frame_kind="decision",
            focus_artifact={
                "primary_focus": "Postgres durability",
                "secondary_focus": [],
                "focus_signals": ["Postgres durability"],
                "weights": {},
                "salience": {},
                "signal_sources": {},
                "frame_kind": "decision",
                "suppressed": [],
            },
        )
        merged = merge_post_reply_reflection(
            base,
            speak_body="Sure, here is a generic answer with no specifics.",
            focus_artifact={"primary_focus": "Postgres durability"},
        )
        self.assertIn(merged["alignment"], {"partial", "misaligned"})
        self.assertTrue(merged["gaps"])


if __name__ == "__main__":
    unittest.main()
