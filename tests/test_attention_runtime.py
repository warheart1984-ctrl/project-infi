"""Tests for Attention Runtime v1.2."""

import unittest

from src.cog_runtime.attention import (
    ATTENTION_RUNTIME_VERSION,
    ATTENTION_STAGES,
    attention_runtime_spec,
    run_attention_turn,
    validate_focus_artifact,
)


class TestAttentionRuntime(unittest.TestCase):
    def test_spec_lists_stages_v12(self):
        spec = attention_runtime_spec()
        self.assertEqual(spec["id"], "cognitive.attention")
        self.assertEqual(spec["version"], ATTENTION_RUNTIME_VERSION)
        self.assertEqual(spec["version"], "1.2")
        self.assertEqual(list(spec["stages"]), list(ATTENTION_STAGES))

    def test_run_attention_produces_focus_artifact(self):
        artifact, session = run_attention_turn(
            "Should I use Redis or Postgres for cache?",
            context={"frame_kind": "decision"},
        )
        validation = validate_focus_artifact(artifact)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertTrue(artifact["primary_focus"])
        self.assertLessEqual(len(artifact["focus_signals"]), 3)
        self.assertIsInstance(artifact["secondary_focus"], list)
        self.assertIsInstance(artifact["salience"], dict)
        self.assertAlmostEqual(sum(artifact["salience"].values()), 1.0, places=2)
        self.assertIsInstance(artifact["signal_sources"], dict)
        turn_validation = session.validate_turn()
        self.assertTrue(turn_validation["valid"], msg=turn_validation["issues"])
        self.assertEqual(turn_validation["completed_stages"], list(ATTENTION_STAGES))

    def test_face_context_influences_primary_focus(self):
        artifact, _ = run_attention_turn(
            "tiny_nova help me decide between rest or work",
            context={
                "frame_kind": "decision",
                "nova_face": {"face_id": "tiny_nova", "scope": "tiny_nova", "tone": "light"},
            },
        )
        self.assertTrue(artifact["primary_focus"])
        sources = artifact["signal_sources"]
        self.assertTrue(any(source == "face" for source in sources.values()))

    def test_memory_cues_tagged_as_memory_source(self):
        artifact, _ = run_attention_turn(
            "What should I do about the cache?",
            context={
                "frame_kind": "decision",
                "memory_cues": [{"text": "Postgres durable cache preference"}],
            },
        )
        self.assertTrue(
            any(source == "memory" for source in artifact["signal_sources"].values())
        )

    def test_secondary_focus_on_close_scores(self):
        artifact, _ = run_attention_turn(
            "Should I use Redis or Postgres for cache?",
            context={"frame_kind": "decision"},
        )
        if len(artifact["focus_signals"]) > 1:
            self.assertIsInstance(artifact["secondary_focus"], list)

    def test_validate_rejects_missing_v12_fields(self):
        validation = validate_focus_artifact(
            {
                "primary_focus": "test",
                "focus_signals": ["test"],
                "weights": {"test": 0.5},
                "frame_kind": "general",
                "suppressed": [],
            }
        )
        self.assertFalse(validation["valid"])
        self.assertIn("missing_salience", validation["issues"])


if __name__ == "__main__":
    unittest.main()
