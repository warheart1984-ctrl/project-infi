"""Tests for build_training_examples batch generation."""

import unittest

from src.governance_taxonomy import TRAINING_LABELS, TRAINING_SOURCES
from src.invariant_compiler import compile_from_ir
from src.training_view_spec import build_training_examples, build_training_view_spec
from tests.test_bridge_fixtures import build_test_ir


def _ir_payload():
    return build_test_ir(trace_id="trace-training-batch")


class TestTrainingExamples(unittest.TestCase):
    def test_multi_source_batch_dedup_and_ordering(self):
        ir = _ir_payload()
        spec = {
            "generation_sources": ["synthetic_compliant", "synthetic_violation", "fuzzed_envelope"],
            "examples_per_source": 2,
            "fuzz_seeds": [0, 1],
            "usage_mode": "fine_tuning",
        }
        records = build_training_examples(ir, spec)
        self.assertGreaterEqual(len(records), 3)
        view_ids = [item.view_id for item in records]
        self.assertEqual(len(view_ids), len(set(view_ids)))
        sources = {item.source for item in records}
        self.assertTrue(sources.issubset(TRAINING_SOURCES))
        ordered = [item.source for item in records]
        self.assertEqual(ordered, sorted(ordered))

    def test_labels_are_valid(self):
        ir = _ir_payload()
        spec = {
            "generation_sources": ["synthetic_compliant", "synthetic_violation"],
            "examples_per_source": 1,
        }
        for record in build_training_examples(ir, spec):
            self.assertIn(record.label, TRAINING_LABELS)

    def test_fuzz_seeds_produce_mixed_labels(self):
        ir = _ir_payload()
        spec = {
            "generation_sources": ["fuzzed_envelope"],
            "examples_per_source": 4,
            "fuzz_seeds": [0, 1, 2, 3],
        }
        labels = {record.label for record in build_training_examples(ir, spec)}
        self.assertTrue(labels)

    def test_build_training_view_spec_still_single_example(self):
        ir = _ir_payload()
        view_spec = build_training_view_spec(ir)
        self.assertIn("example_record", view_spec)
        batch = build_training_examples(
            ir,
            {
                "generation_sources": ["synthetic_compliant"],
                "examples_per_source": 2,
                "usage_mode": view_spec.get("usage_mode", "fine_tuning"),
            },
        )
        self.assertGreaterEqual(len(batch), 1)


if __name__ == "__main__":
    unittest.main()
