"""Tests for Memory Runtime v1.2 episodic compression and semantic abstraction."""

import unittest

from src.cog_runtime.memory import (
    EPISODIC_KIND,
    MEMORY_RUNTIME_VERSION,
    _abstract_semantic_records,
    _compress_episodic_records,
    memory_runtime_spec,
    normalize_cortex_memory_cues,
    run_memory_turn,
    validate_memory_artifact,
)


class TestMemoryRuntimeV12(unittest.TestCase):
    def test_spec_version_v12(self):
        spec = memory_runtime_spec()
        self.assertEqual(spec["version"], "1.2")
        self.assertEqual(MEMORY_RUNTIME_VERSION, "1.2")

    def test_compress_episodic_records(self):
        compressed = _compress_episodic_records(
            [
                {"id": "e1", "text": "User asked about Postgres cache durability today"},
                {"id": "e2", "text": "Postgres latency test results from earlier"},
            ]
        )
        self.assertEqual(len(compressed), 1)
        self.assertIn("summary", compressed[0])
        self.assertEqual(compressed[0]["record_count"], 2)

    def test_abstract_semantic_records(self):
        abstractions = _abstract_semantic_records(
            [{"id": "s1", "text": "Postgres is the durable cache preference for this user"}]
        )
        self.assertTrue(abstractions)
        self.assertIn("abstract", abstractions[0])

    def test_run_memory_turn_emits_compression_and_abstraction(self):
        _, artifact, session = run_memory_turn(
            "What cache should we use today?",
            memory_cues=[{"id": "pref-1", "text": "Postgres is the durable cache preference"}],
            focus_artifact={
                "primary_focus": "cache choice",
                "secondary_focus": [],
                "focus_signals": ["cache choice"],
                "weights": {},
                "salience": {},
                "signal_sources": {},
                "frame_kind": "decision",
                "suppressed": [],
            },
            frame_kind="decision",
        )
        validation = validate_memory_artifact(artifact)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertTrue(artifact["compressed_episodic"])
        self.assertTrue(artifact["semantic_abstractions"])
        self.assertEqual(artifact["encoded"]["memory_kind"], EPISODIC_KIND)
        self.assertTrue(session.validate_turn()["valid"])

    def test_normalize_cortex_memory_cues_reads_memory_board(self):
        board = {
            "slots": [
                {
                    "slot_id": "continuity",
                    "active": True,
                    "module": {
                        "module_id": "continuity_v1",
                        "summary": "Operator prefers Postgres for durable cache.",
                    },
                },
                {
                    "slot_id": "reserved",
                    "active": False,
                    "module": {
                        "module_id": "ignored",
                        "summary": "Should not surface",
                    },
                },
            ]
        }
        cues = normalize_cortex_memory_cues(board)
        texts = [str(item.get("text") if isinstance(item, dict) else item) for item in cues]
        self.assertIn("Operator prefers Postgres for durable cache.", texts)
        self.assertEqual(len(cues), 1)


if __name__ == "__main__":
    unittest.main()
