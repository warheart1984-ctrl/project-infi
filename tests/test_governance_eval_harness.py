"""Tests for governance eval harness."""

import unittest

from src.governance_eval_harness import assert_label_parity, replay_label, run_eval_suite
from src.training_view_spec import (
    TrainingViewRecord,
    build_training_examples,
    project_synthetic,
)
from tests.test_bridge_fixtures import build_test_ir


def _ir():
    return build_test_ir(trace_id="trace-eval-harness")


class TestGovernanceEvalHarness(unittest.TestCase):
    def test_label_parity_passes_on_synthetic_suite(self):
        ir = _ir()
        examples = build_training_examples(
            ir,
            {
                "generation_sources": ["synthetic_compliant", "synthetic_violation"],
                "examples_per_source": 1,
            },
        )
        summary = run_eval_suite(examples, include_runtime=False)
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["label_parity"]["fail"], 0)

    def test_injected_mismatch_fails(self):
        ir = _ir()
        record = project_synthetic(ir, label="COMPLIANT")
        bad = TrainingViewRecord(
            view_id=record.view_id,
            ir_fingerprint=record.ir_fingerprint,
            input_text=record.input_text,
            conversation_window=record.conversation_window,
            governance_ir_snapshot=record.governance_ir_snapshot,
            label="VIOLATION",
            action_type=record.action_type,
            resource_class=record.resource_class,
            authority_delta=record.authority_delta,
            source=record.source,
            usage_mode=record.usage_mode,
        )
        parity = assert_label_parity(bad)
        self.assertEqual(parity["status"], "fail")
        self.assertEqual(replay_label(bad), "COMPLIANT")

    def test_optional_mock_runtime_path(self):
        ir = _ir()
        examples = build_training_examples(
            ir,
            {"generation_sources": ["synthetic_compliant"], "examples_per_source": 1},
        )
        summary = run_eval_suite(examples, include_runtime=True, provider_id="reference_mock")
        self.assertTrue(summary["runtime_replay"]["enabled"])
        self.assertGreaterEqual(summary["runtime_replay"]["pass"], 1)


if __name__ == "__main__":
    unittest.main()
